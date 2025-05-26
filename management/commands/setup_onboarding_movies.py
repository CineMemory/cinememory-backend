from django.core.management.base import BaseCommand
from movies.models import Movie

class Command(BaseCommand):
    help = '온보딩용 영화 30개 설정'
    
    def handle(self, *args, **options):
        # 인기 영화들을 온보딩용으로 설정
        popular_movies = [
            # 액션 (우선순위 1-5)
            {'movie_id': 155, 'category': '액션', 'priority': 1},  # 다크 나이트
            {'movie_id': 24428, 'category': '액션', 'priority': 2},  # 어벤져스
            
            # 드라마 (우선순위 6-10)
            {'movie_id': 278, 'category': '드라마', 'priority': 6},  # 쇼생크 탈출
            {'movie_id': 238, 'category': '드라마', 'priority': 7},  # 대부
            
            # 코미디 (우선순위 11-15)
            {'movie_id': 862, 'category': '코미디', 'priority': 11},  # 토이 스토리
            
            # SF (우선순위 16-20)
            {'movie_id': 603, 'category': 'SF', 'priority': 16},  # 매트릭스
            {'movie_id': 27205, 'category': 'SF', 'priority': 17},  # 인셉션
            
            # 로맨스 (우선순위 21-25)
            {'movie_id': 597, 'category': '로맨스', 'priority': 21},  # 타이타닉
            
            # 애니메이션 (우선순위 26-30)
            {'movie_id': 12, 'category': '애니메이션', 'priority': 26},  # 니모를 찾아서
            {'movie_id': 10681, 'category': '애니메이션', 'priority': 27},  # 월-E
        ]
        
        updated_count = 0
        for movie_data in popular_movies:
            try:
                movie = Movie.objects.get(movie_id=movie_data['movie_id'])
                movie.is_onboarding_movie = True
                movie.onboarding_priority = movie_data['priority']
                movie.onboarding_category = movie_data['category']
                movie.save()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ 온보딩 영화 설정: {movie.title} ({movie_data['category']})"
                    )
                )
                updated_count += 1
                
            except Movie.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️  영화를 찾을 수 없음: movie_id {movie_data['movie_id']}"
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(f"🎬 총 {updated_count}개의 온보딩 영화가 설정되었습니다.")
        )