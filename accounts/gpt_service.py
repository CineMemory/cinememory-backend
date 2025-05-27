import json
import openai
import re
from django.conf import settings
from datetime import datetime
import random
from movies.models import Movie


class GPTRecommendationService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_recommendations(
        self, user, favorite_movies, interesting_movies, excluded_genres
    ):
        """OpenAI GPT를 사용하여 영화 추천 생성"""

        # 프롬프트 생성
        prompt = self._create_recommendation_prompt(
            user, favorite_movies, interesting_movies, excluded_genres
        )

        try:
            # OpenAI API 호출
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # 올바른 모델명으로 수정
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 영화 추천 전문가입니다. 사용자의 취향을 분석하고 개인화된 영화를 추천해주세요. 반드시 요청된 JSON 형식으로 응답해주세요.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
            )

            # 응답 파싱
            gpt_response = response.choices[0].message.content
            return self._parse_gpt_response(gpt_response, user)

        except Exception as e:
            print(f"OpenAI API 오류: {str(e)}")
            # API 오류 시 폴백으로 더미 데이터 반환
            return self._generate_fallback_recommendation(user)

    def _create_recommendation_prompt(
        self, user, favorite_movies, interesting_movies, excluded_genres
    ):
        """GPT 프롬프트 생성"""
        birth_year = user.birth.year
        current_year = datetime.now().year
        age = current_year - birth_year
        username = user.username

        favorite_titles = [
            f"{movie.movie.title} ({movie.movie.release_date.year if movie.movie.release_date else 'N/A'})"
            for movie in favorite_movies
        ]
        interesting_titles = [
            f"{movie.movie.title} ({movie.movie.release_date.year if movie.movie.release_date else 'N/A'})"
            for movie in interesting_movies
        ]
        excluded_genre_names = [genre.genre.name for genre in excluded_genres]

        prompt = f"""
            사용자 정보 분석 및 영화 추천 요청:

            **사용자 프로필:**
            - 이름: {username}
            - 출생년도: {birth_year}년
            - 현재 나이: {age}세
            - 성인 여부: {'성인' if user.is_adult else '미성년자'}

            **재밌게 본 영화들:**
            {', '.join(favorite_titles) if favorite_titles else '선택 안함'}

            **재밌어 보이는 영화들:**
            {', '.join(interesting_titles) if interesting_titles else '선택 안함'}

            **제외할 장르:**
            {', '.join(excluded_genre_names) if excluded_genre_names else '없음'}

            **요청사항:**
            1. 사용자의 영화 취향을 분석하여 개성 있는 취향 분석 텍스트를 작성해주세요.
            - 형식: "{username}님은 [구체적인 취향 분석] 취향이시네요."
            - 단순한 장르 나열이 아닌, 영화를 통해 추구하는 가치나 선호하는 스토리텔링 방식 등을 포함해주세요.

            2. {birth_year}년 이후 개봉한 영화 중에서 사용자의 취향과 비슷한 맞는 영화 6개 추천.
            - 다양한 개봉 연도의 영화를 포함해주세요.
            - 제외 장르는 피해서 추천해주세요.
            - 각 영화에 대해 사용자의 몇 살 때 개봉했는지 계산해주세요. (target_age는 반드시 숫자만 입력)

            3. 각 영화별로 왜 이 사용자에게 맞는지 구체적인 추천 근거를 제시해주세요.

            **응답 형식 (반드시 JSON 형태로):**
            ```json
            {{
            "taste_summary": "취향 분석한 결과 텍스트",
            "movies": [
                {{
                "movie_id": "영화 고유 번호1",
                "title": "영화 제목1",
                "release_year": "개봉년도1",
                "reason": "이 영화를 추천하는 구체적 이유1",
                "target_age": 숫자만입력
                }},
                {{
                "movie_id": "영화 고유 번호2",
                "title": "영화 제목2",
                "release_year": "개봉년도2",
                "reason": "이 영화를 추천하는 구체적 이유2",
                "target_age": 숫자만입력
                }},
                ...
            ]
            }}
            ```
            실제 존재하는 영화만 추천해주시고, 추천 근거는 사용자가 선택한 영화들과의 연관성을 바탕으로 구체적으로 작성해주세요.
            """

        return prompt

    def _parse_gpt_response(self, gpt_response, user):
        """GPT 응답을 파싱하여 구조화된 데이터로 변환"""
        try:
            # JSON 부분만 추출
            start_idx = gpt_response.find('{')
            end_idx = gpt_response.rfind('}') + 1

            if start_idx == -1 or end_idx == 0:
                raise ValueError("JSON 형식을 찾을 수 없습니다.")

            json_str = gpt_response[start_idx:end_idx]
            parsed_data = json.loads(json_str)

            # 영화 데이터를 실제 DB의 영화와 매칭
            movies_with_ids = []
            for movie_data in parsed_data.get('movies', []):
                title = movie_data.get('title', '')
                release_year = movie_data.get('release_year')

                # 제목과 연도를 기반으로 영화 검색
                matching_movie = self._find_matching_movie(title, release_year)

                if matching_movie:
                    # target_age 값을 정수로 변환
                    target_age_raw = movie_data.get('target_age', '20')
                    # 문자열에서 숫자만 추출 (예: "7세" -> 7)
                    if isinstance(target_age_raw, str):
                        age_match = re.search(r'\d+', str(target_age_raw))
                        target_age = (
                            int(age_match.group()) if age_match else 20
                        )
                    else:
                        target_age = (
                            int(target_age_raw) if target_age_raw else 20
                        )

                    movies_with_ids.append(
                        {
                            'movie_id': matching_movie.id,
                            'title': matching_movie.title,
                            'reason': movie_data.get('reason', '추천 근거'),
                            'target_age': target_age,
                        }
                    )

            return {
                'taste_summary': parsed_data.get(
                    'taste_summary',
                    f'{user.username}님의 취향을 분석했습니다.',
                ),
                'movies': movies_with_ids[:6],  # 최대 6개
            }

        except Exception as e:
            print(f"GPT 응답 파싱 오류: {str(e)}")
            return self._generate_fallback_recommendation(user)

    def _find_matching_movie(self, title, release_year):
        """제목과 연도를 기반으로 DB에서 영화 검색"""
        try:
            # 정확한 제목 매칭 시도
            if release_year:
                release_date_start = f"{release_year}-01-01"
                release_date_end = f"{release_year}-12-31"

                movie = Movie.objects.filter(
                    title__icontains=title,
                    release_date__gte=release_date_start,
                    release_date__lte=release_date_end,
                ).first()

                if movie:
                    return movie

            # 제목만으로 검색
            movie = Movie.objects.filter(title__icontains=title).first()
            if movie:
                return movie

            # 부분 제목 매칭
            words = title.split()
            for word in words:
                if len(word) > 2:  # 의미있는 단어만
                    movie = Movie.objects.filter(title__icontains=word).first()
                    if movie:
                        return movie

            return None

        except Exception as e:
            print(f"영화 검색 오류: {str(e)}")
            return None

    def _generate_fallback_recommendation(self, user):
        """API 오류 시 폴백 추천 생성"""
        # 인기 영화들 중에서 랜덤 추천
        popular_movies = Movie.objects.filter(popularity__gt=50).order_by(
            '-popularity'
        )[:20]

        selected_movies = random.sample(
            list(popular_movies), min(6, len(popular_movies))
        )

        movies_data = []
        for i, movie in enumerate(selected_movies, 1):
            target_age = (
                2024 - user.birth.year - (2024 - movie.release_date.year)
                if movie.release_date
                else 20
            )
            movies_data.append(
                {
                    'movie_id': movie.id,  # movie_id를 id로 변경
                    'title': movie.title,
                    'reason': f'{movie.title}은 많은 사람들에게 사랑받는 작품으로, 당신의 취향에도 잘 맞을 것 같습니다.',
                    'target_age': max(target_age, 10),
                }
            )

        return {
            'taste_summary': f"{user.username}님의 설문을 기반으로 취향을 파악해봤습니다! \n{user.username}은 다양한 장르를 즐기는 열린 취향이시네요.",
            'movies': movies_data,
        }
