# Integration test script for the RealTime AI Dubbing system
import asyncio
import json
import websockets
import base64
import numpy as np
from typing import Dict, Any

class RTDIntegrationTest:
    def __init__(self):
        self.server_url = "ws://localhost:8000/ws"
        self.test_results = []
        
    async def test_websocket_connection(self) -> bool:
        """Test basic WebSocket connection to backend server"""
        try:
            async with websockets.connect(self.server_url) as websocket:
                # Send test message
                test_config = {
                    "type": "config",
                    "settings": {
                        "targetLanguage": "en",
                        "voicePreservation": "auto"
                    },
                    "platform": "test"
                }
                
                await websocket.send(json.dumps(test_config))
                
                # Wait for response
                response = await websocket.recv()
                data = json.loads(response)
                
                return data.get("type") == "config_ack"
                
        except Exception as e:
            print(f"WebSocket connection test failed: {e}")
            return False
    
    async def test_audio_processing(self) -> bool:
        """Test audio chunk processing pipeline"""
        try:
            # Generate test audio data (sine wave)
            sample_rate = 44100
            duration = 1.0  # 1 second
            frequency = 440  # A4 note
            
            t = np.linspace(0, duration, int(sample_rate * duration))
            audio_data = np.sin(2 * np.pi * frequency * t) * 0.5
            
            async with websockets.connect(self.server_url) as websocket:
                # Send configuration
                config = {
                    "type": "config",
                    "settings": {
                        "targetLanguage": "es",  # Test translation
                        "voicePreservation": "auto"
                    },
                    "platform": "test"
                }
                await websocket.send(json.dumps(config))
                
                # Send audio chunk
                audio_chunk = {
                    "type": "audio_chunk",
                    "data": audio_data.tolist(),
                    "sampleRate": sample_rate,
                    "timestamp": 1234567890000
                }
                
                await websocket.send(json.dumps(audio_chunk))
                
                # Wait for processed response
                timeout_count = 0
                while timeout_count < 10:  # 10 second timeout
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(response)
                        
                        if data.get("type") == "dubbed_audio":
                            return True
                        elif data.get("type") == "error":
                            print(f"Server error: {data.get('error')}")
                            return False
                            
                    except asyncio.TimeoutError:
                        timeout_count += 1
                        continue
                
                return False
                
        except Exception as e:
            print(f"Audio processing test failed: {e}")
            return False
    
    def test_extension_files(self) -> bool:
        """Test that all required extension files exist"""
        required_files = [
            '/workspace/code/realtime_dubbing/extension/manifest.json',
            '/workspace/code/realtime_dubbing/extension/popup.html',
            '/workspace/code/realtime_dubbing/extension/popup.js',
            '/workspace/code/realtime_dubbing/extension/background.js',
            '/workspace/code/realtime_dubbing/extension/content.js',
            '/workspace/code/realtime_dubbing/extension/audio-processor.js',
            '/workspace/code/realtime_dubbing/extension/styles.css',
            '/workspace/code/realtime_dubbing/extension/icons/icon-16.png',
            '/workspace/code/realtime_dubbing/extension/icons/icon-48.png',
            '/workspace/code/realtime_dubbing/extension/icons/icon-128.png'
        ]
        
        import os
        missing_files = []
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            print(f"Missing extension files: {missing_files}")
            return False
        
        return True
    
    def test_manifest_validity(self) -> bool:
        """Test that manifest.json is valid"""
        try:
            with open('/workspace/code/realtime_dubbing/extension/manifest.json', 'r') as f:
                manifest = json.load(f)
            
            required_keys = ['manifest_version', 'name', 'version', 'permissions', 'content_scripts']
            
            for key in required_keys:
                if key not in manifest:
                    print(f"Missing required key in manifest: {key}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"Manifest validation failed: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all integration tests"""
        results = {}
        
        print("Running RTD Integration Tests...\n")
        
        # Test 1: Extension files
        print("1. Testing extension files...")
        results['extension_files'] = self.test_extension_files()
        print(f"   Result: {'PASS' if results['extension_files'] else 'FAIL'}\n")
        
        # Test 2: Manifest validity
        print("2. Testing manifest validity...")
        results['manifest_validity'] = self.test_manifest_validity()
        print(f"   Result: {'PASS' if results['manifest_validity'] else 'FAIL'}\n")
        
        # Test 3: WebSocket connection (requires server)
        print("3. Testing WebSocket connection...")
        results['websocket_connection'] = await self.test_websocket_connection()
        print(f"   Result: {'PASS' if results['websocket_connection'] else 'FAIL'}\n")
        
        # Test 4: Audio processing (requires server)
        if results['websocket_connection']:
            print("4. Testing audio processing...")
            results['audio_processing'] = await self.test_audio_processing()
            print(f"   Result: {'PASS' if results['audio_processing'] else 'FAIL'}\n")
        else:
            print("4. Skipping audio processing test (server not available)\n")
            results['audio_processing'] = False
        
        return results
    
    def print_summary(self, results: Dict[str, bool]):
        """Print test summary"""
        print("=" * 50)
        print("INTEGRATION TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        
        for test_name, result in results.items():
            status = "PASS" if result else "FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("\n✅ All tests passed! Extension is ready for use.")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Check the issues above.")

# Run tests if executed directly
if __name__ == "__main__":
    async def main():
        tester = RTDIntegrationTest()
        results = await tester.run_all_tests()
        tester.print_summary(results)
    
    asyncio.run(main())