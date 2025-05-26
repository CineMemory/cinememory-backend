# 📁 movies/management/commands/load_test_data.py
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
import os
from movies.models import Movie, Actor, Director, Genre, WatchProvider, MovieWatchProvider


class Command(BaseCommand):
    help = '씨네메모리 테스트 데이터를 로드합니다 (스트리밍 정보 포함)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='기존 데이터를 모두 삭제하고 새로 로드합니다',
        )
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='사용자 입력 없이 자동으로 실행합니다',
        )
    
    def handle(self, *args, **options):
        self.stdout.write("🎬 씨네메모리 테스트 데이터 로딩 시작...")
        self.stdout.write("=" * 50)
        
        # 데이터베이스 초기화 확인
        if options['flush']:
            self.stdout.write("🔄 데이터베이스 초기화 중...")
            call_command('flush', '--noinput')
            self.stdout.write(
                self.style.SUCCESS('✅ 데이터베이스 초기화 완료')
            )
        elif not options['no_input']:
            confirm = input("🗑️  기존 데이터를 모두 삭제하고 새로 로드하시겠습니까? (y/N): ")
            if confirm.lower() in ['y', 'yes']:
                self.stdout.write("🔄 데이터베이스 초기화 중...")
                call_command('flush', '--noinput')
                self.stdout.write(
                    self.style.SUCCESS('✅ 데이터베이스 초기화 완료')
                )
        
        # Fixture 파일 목록 (순서 중요!)
        fixtures = [
            ('genres_fixtures.json', '장르'),
            ('series_fixtures.json', '시리즈'),
            ('directors_fixtures.json', '감독'),
            ('actors_fixtures.json', '배우'),
            ('watch_providers_fixtures.json', '스트리밍 제공업체'),
            ('movies_fixtures.json', '영화'),
            ('manytomany_fixtures.json', '관계 데이터'),
        ]
        
        # 각 fixture 파일 로드
        with transaction.atomic():
            for fixture_file, description in fixtures:
                fixture_path = f'movies/fixtures/{fixture_file}'
                
                if os.path.exists(fixture_path):
                    self.stdout.write(f'📦 로딩 중: {description} ({fixture_file})')
                    
                    try:
                        call_command('loaddata', fixture_file)
                        self.stdout.write(
                            self.style.SUCCESS(f'✅ {description} 로드 완료')
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'❌ {description} 로드 실패: {e}')
                        )
                        return
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  파일 없음: {fixture_path}')
                    )
                
                self.stdout.write("---")
        
        # 최종 통계
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS('🎉 모든 테스트 데이터 로드 완료!')
        )
        
        self.stdout.write("📊 데이터 통계:")
        self.stdout.write(f'   - 영화: {Movie.objects.count()}개')
        self.stdout.write(f'   - 배우: {Actor.objects.count()}명')
        self.stdout.write(f'   - 감독: {Director.objects.count()}명')
        self.stdout.write(f'   - 장르: {Genre.objects.count()}개')
        self.stdout.write(f'   - 스트리밍 제공업체: {WatchProvider.objects.count()}개')
        self.stdout.write(f'   - 스트리밍 관계: {MovieWatchProvider.objects.count()}개')
        
        self.stdout.write("")
        self.stdout.write("🚀 씨네메모리 개발 서버를 시작하세요:")
        self.stdout.write("   python manage.py runserver")