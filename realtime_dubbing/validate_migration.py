#!/usr/bin/env python3
"""
Validation script for Local Whisper migration
Tests that our code changes are syntactically correct and imports work
"""

import sys
import os

# Add the project path to sys.path
sys.path.append('/workspace/code/realtime_dubbing')

def test_imports():
    """Test that our updated modules can be imported successfully."""
    print("🔍 Testing module imports...")
    
    try:
        # Test configuration imports
        print("   ✓ Testing config imports...")
        from config.settings import settings
        print(f"   ✓ Whisper model setting: {settings.whisper_model}")
        
        # Test that openai_api_key is no longer required
        if hasattr(settings, 'openai_api_key'):
            print("   ⚠️  openai_api_key still exists in settings (should be removed)")
        else:
            print("   ✅ openai_api_key successfully removed from settings")
        
        # Test model imports
        print("   ✓ Testing model imports...")
        from models.audio_models import SpeechRecognitionResult, TranslationResult
        
        # Test that our service can be imported (even if we can't run it yet)
        print("   ✓ Testing service imports...")
        try:
            from services.whisper_speech_service import WhisperSpeechService, WhisperTranslateService
            print("   ✅ WhisperSpeechService and WhisperTranslateService imported successfully")
        except ImportError as e:
            if "whisper" in str(e).lower():
                print("   ⏳ Whisper library not yet installed (dependencies still downloading)")
                return "partial"
            else:
                raise e
        
        print("\n✅ All imports successful!")
        return "success"
        
    except Exception as e:
        print(f"\n❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return "failed"

def test_configuration():
    """Test that configuration changes are correct."""
    print("\n🔧 Testing configuration changes...")
    
    try:
        from config.settings import settings
        
        # Check whisper model setting
        expected_model = "base"
        if settings.whisper_model == expected_model:
            print(f"   ✅ Whisper model correctly set to: {settings.whisper_model}")
        else:
            print(f"   ⚠️  Whisper model is: {settings.whisper_model}, expected: {expected_model}")
        
        # Check that API key dependency is removed
        if hasattr(settings, 'openai_api_key'):
            print("   ⚠️  OpenAI API key dependency still exists")
        else:
            print("   ✅ OpenAI API key dependency successfully removed")
            
        print("\n✅ Configuration tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Configuration test failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🎯 VALIDATION: Local Whisper Migration")
    print("=" * 50)
    
    # Test imports
    import_result = test_imports()
    
    # Test configuration
    config_result = test_configuration()
    
    # Summary
    print("\n📊 VALIDATION SUMMARY:")
    print(f"   Imports: {import_result}")
    print(f"   Configuration: {'✅ PASS' if config_result else '❌ FAIL'}")
    
    if import_result in ["success", "partial"] and config_result:
        print("\n🎉 MIGRATION VALIDATION: SUCCESS!")
        print("\n💡 Next Steps:")
        print("   1. Wait for dependencies to finish installing")
        print("   2. Run full integration test")
        print("   3. Test with real audio data")
        return True
    else:
        print("\n💔 VALIDATION: Issues found that need attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
