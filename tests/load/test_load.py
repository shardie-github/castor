"""
Load Testing Suite

Enterprise-grade load testing with:
- Baseline performance tests
- Stress tests
- Spike tests
- Endurance tests
- Capacity planning
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
import httpx
import logging

logger = logging.getLogger(__name__)


class LoadTestResult:
    """Load test result"""
    
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times: List[float] = []
        self.status_codes: Dict[int, int] = {}
        self.errors: List[str] = []
        self.start_time: float = 0
        self.end_time: float = 0
        self.duration: float = 0
    
    def add_request(self, response_time: float, status_code: int, error: Optional[str] = None):
        """Add request result"""
        self.total_requests += 1
        self.response_times.append(response_time)
        self.status_codes[status_code] = self.status_codes.get(status_code, 0) + 1
        
        if status_code < 400:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
            if error:
                self.errors.append(error)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        if not self.response_times:
            return {}
        
        sorted_times = sorted(self.response_times)
        
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.successful_requests / self.total_requests if self.total_requests > 0 else 0,
            "duration": self.duration,
            "requests_per_second": self.total_requests / self.duration if self.duration > 0 else 0,
            "response_time": {
                "min": min(self.response_times),
                "max": max(self.response_times),
                "mean": statistics.mean(self.response_times),
                "median": statistics.median(self.response_times),
                "p95": sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0,
                "p99": sorted_times[int(len(sorted_times) * 0.99)] if sorted_times else 0,
            },
            "status_codes": self.status_codes,
            "error_count": len(self.errors),
        }


class LoadTester:
    """Load testing framework"""
    
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url
        self.timeout = timeout
    
    async def baseline_test(
        self,
        endpoint: str,
        method: str = "GET",
        concurrent_users: int = 10,
        requests_per_user: int = 10,
        **kwargs
    ) -> LoadTestResult:
        """
        Baseline performance test.
        
        Simulates normal load to establish performance baseline.
        """
        result = LoadTestResult()
        result.start_time = time.time()
        
        async def make_request(client: httpx.AsyncClient):
            """Make a single request"""
            start = time.time()
            try:
                if method == "GET":
                    response = await client.get(endpoint, timeout=self.timeout, **kwargs)
                elif method == "POST":
                    response = await client.post(endpoint, timeout=self.timeout, **kwargs)
                else:
                    response = await client.request(method, endpoint, timeout=self.timeout, **kwargs)
                
                response_time = time.time() - start
                result.add_request(response_time, response.status_code)
            except Exception as e:
                response_time = time.time() - start
                result.add_request(response_time, 0, str(e))
        
        # Create clients for concurrent users
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            tasks = []
            for _ in range(concurrent_users):
                for _ in range(requests_per_user):
                    tasks.append(make_request(client))
            
            await asyncio.gather(*tasks)
        
        result.end_time = time.time()
        result.duration = result.end_time - result.start_time
        
        return result
    
    async def stress_test(
        self,
        endpoint: str,
        method: str = "GET",
        max_users: int = 100,
        ramp_up_time: int = 60,  # seconds
        **kwargs
    ) -> LoadTestResult:
        """
        Stress test.
        
        Gradually increases load to find breaking point.
        """
        result = LoadTestResult()
        result.start_time = time.time()
        
        users_per_second = max_users / ramp_up_time
        current_users = 0
        
        async def make_request(client: httpx.AsyncClient):
            """Make a single request"""
            start = time.time()
            try:
                if method == "GET":
                    response = await client.get(endpoint, timeout=self.timeout, **kwargs)
                else:
                    response = await client.request(method, endpoint, timeout=self.timeout, **kwargs)
                
                response_time = time.time() - start
                result.add_request(response_time, response.status_code)
            except Exception as e:
                response_time = time.time() - start
                result.add_request(response_time, 0, str(e))
        
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            tasks = []
            start_time = time.time()
            
            while current_users < max_users:
                elapsed = time.time() - start_time
                target_users = int(users_per_second * elapsed)
                
                # Add new users
                while current_users < target_users and current_users < max_users:
                    tasks.append(make_request(client))
                    current_users += 1
                
                await asyncio.sleep(0.1)
            
            await asyncio.gather(*tasks)
        
        result.end_time = time.time()
        result.duration = result.end_time - result.start_time
        
        return result
    
    async def spike_test(
        self,
        endpoint: str,
        method: str = "GET",
        spike_users: int = 200,
        spike_duration: int = 30,  # seconds
        **kwargs
    ) -> LoadTestResult:
        """
        Spike test.
        
        Sudden increase in load to test system resilience.
        """
        result = LoadTestResult()
        result.start_time = time.time()
        
        async def make_request(client: httpx.AsyncClient):
            """Make a single request"""
            start = time.time()
            try:
                if method == "GET":
                    response = await client.get(endpoint, timeout=self.timeout, **kwargs)
                else:
                    response = await client.request(method, endpoint, timeout=self.timeout, **kwargs)
                
                response_time = time.time() - start
                result.add_request(response_time, response.status_code)
            except Exception as e:
                response_time = time.time() - start
                result.add_request(response_time, 0, str(e))
        
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            tasks = []
            end_time = time.time() + spike_duration
            
            # Create spike
            while time.time() < end_time:
                for _ in range(spike_users):
                    tasks.append(make_request(client))
                await asyncio.sleep(1)
            
            await asyncio.gather(*tasks)
        
        result.end_time = time.time()
        result.duration = result.end_time - result.start_time
        
        return result


# Example usage
async def run_load_tests():
    """Run load tests"""
    tester = LoadTester("http://localhost:8000")
    
    print("Running baseline test...")
    baseline = await tester.baseline_test("/health", concurrent_users=10, requests_per_user=10)
    print(f"Baseline: {baseline.get_stats()}")
    
    print("Running stress test...")
    stress = await tester.stress_test("/health", max_users=50, ramp_up_time=30)
    print(f"Stress: {stress.get_stats()}")
    
    print("Running spike test...")
    spike = await tester.spike_test("/health", spike_users=100, spike_duration=10)
    print(f"Spike: {spike.get_stats()}")


if __name__ == "__main__":
    asyncio.run(run_load_tests())
