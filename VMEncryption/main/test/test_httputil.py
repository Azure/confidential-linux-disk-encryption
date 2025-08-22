#!/usr/bin/env python

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add the parent directory to the path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from HttpUtil import HttpUtil


class TestHttpUtil(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_logger = Mock()
        
        # Mock waagent loading
        self.mock_waagent = Mock()
        self.mock_config = Mock()
        self.mock_config.get.side_effect = lambda key: {
            "HttpProxy.Host": None,
            "HttpProxy.Port": None
        }.get(key)
        
        with patch('HttpUtil.load_waagent', return_value=self.mock_waagent):
            with patch.object(self.mock_waagent, 'ConfigurationProvider', return_value=self.mock_config):
                self.http_util = HttpUtil(self.mock_logger)

    def test_init_no_proxy(self):
        """Test HttpUtil initialization without proxy"""
        self.assertIsNone(self.http_util.proxyHost)
        self.assertIsNone(self.http_util.proxyPort)
        self.assertIsNone(self.http_util.connection)

    def test_init_with_proxy(self):
        """Test HttpUtil initialization with proxy"""
        mock_config = Mock()
        mock_config.get.side_effect = lambda key: {
            "HttpProxy.Host": "proxy.example.com",
            "HttpProxy.Port": "8080"
        }.get(key)
        
        with patch('HttpUtil.load_waagent', return_value=self.mock_waagent):
            with patch.object(self.mock_waagent, 'ConfigurationProvider', return_value=mock_config):
                http_util = HttpUtil(self.mock_logger)
                
        self.assertEqual(http_util.proxyHost, "proxy.example.com")
        self.assertEqual(http_util.proxyPort, "8080")

    def test_init_waagent_exception(self):
        """Test HttpUtil initialization when waagent throws exception"""
        mock_waagent = Mock()
        mock_waagent.GetMyDistro.side_effect = Exception("Waagent error")
        mock_config = Mock()
        mock_config.get.return_value = None
        
        with patch('HttpUtil.load_waagent', return_value=mock_waagent):
            with patch.object(mock_waagent, 'ConfigurationProvider', return_value=mock_config):
                http_util = HttpUtil(self.mock_logger)
                
        self.mock_logger.log.assert_called_with(
            "Failed to construct ConfigurationProvider, which may due to the old wala code."
        )

    @patch('HttpUtil.httpclient.HTTPSConnection')
    @patch('HttpUtil.urlparse')
    def test_call_https_no_proxy(self, mock_urlparse, mock_https_connection):
        """Test Call method with HTTPS and no proxy"""
        # Setup URL parsing
        mock_uri = Mock()
        mock_uri.hostname = "example.com"
        mock_uri.path = "/api/test"
        mock_uri.query = "param=value"
        mock_urlparse.return_value = mock_uri
        
        # Setup connection mock
        mock_connection = Mock()
        mock_response = Mock()
        mock_connection.getresponse.return_value = mock_response
        mock_https_connection.return_value = mock_connection
        
        # Call the method
        result = self.http_util.Call(
            method="GET",
            http_uri="https://example.com/api/test?param=value",
            data=None,
            headers={"Content-Type": "application/json"},
            use_https=True
        )
        
        # Verify
        mock_https_connection.assert_called_once_with("example.com", timeout=60)
        mock_connection.request.assert_called_once_with(
            method="GET",
            url="/api/test?param=value",
            body=None,
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(result, mock_response)

    @patch('HttpUtil.httpclient.HTTPConnection')
    @patch('HttpUtil.urlparse')
    def test_call_http_no_proxy(self, mock_urlparse, mock_http_connection):
        """Test Call method with HTTP and no proxy"""
        # Setup URL parsing
        mock_uri = Mock()
        mock_uri.hostname = "example.com"
        mock_uri.path = "/api/test"
        mock_uri.query = None
        mock_urlparse.return_value = mock_uri
        
        # Setup connection mock
        mock_connection = Mock()
        mock_response = Mock()
        mock_connection.getresponse.return_value = mock_response
        mock_http_connection.return_value = mock_connection
        
        # Call the method
        result = self.http_util.Call(
            method="POST",
            http_uri="http://example.com/api/test",
            data="test data",
            headers={"Content-Type": "text/plain"},
            use_https=False
        )
        
        # Verify
        mock_http_connection.assert_called_once_with("example.com", timeout=60)
        mock_connection.request.assert_called_once_with(
            method="POST",
            url="/api/test",
            body="test data",
            headers={"Content-Type": "text/plain"}
        )
        self.assertEqual(result, mock_response)

    @patch('HttpUtil.httpclient.HTTPSConnection')
    @patch('HttpUtil.urlparse')
    def test_call_with_proxy_https(self, mock_urlparse, mock_https_connection):
        """Test Call method with HTTPS and proxy"""
        # Setup proxy
        self.http_util.proxyHost = "proxy.example.com"
        self.http_util.proxyPort = "8080"
        
        # Setup URL parsing
        mock_uri = Mock()
        mock_uri.hostname = "api.example.com"
        mock_uri.scheme = "https"
        mock_urlparse.return_value = mock_uri
        
        # Setup connection mock
        mock_connection = Mock()
        mock_response = Mock()
        mock_connection.getresponse.return_value = mock_response
        mock_https_connection.return_value = mock_connection
        
        # Call the method
        result = self.http_util.Call(
            method="GET",
            http_uri="https://api.example.com/test",
            data=None,
            headers={},
            use_https=True
        )
        
        # Verify
        mock_https_connection.assert_called_once_with("proxy.example.com", "8080", timeout=60)
        mock_connection.set_tunnel.assert_called_once_with("api.example.com", 443)
        mock_connection.request.assert_called_once_with(
            method="GET",
            url="https://api.example.com/test",
            body=None,
            headers={}
        )
        self.assertEqual(result, mock_response)

    @patch('HttpUtil.httpclient.HTTPSConnection')
    @patch('HttpUtil.urlparse')
    def test_call_with_proxy_http(self, mock_urlparse, mock_https_connection):
        """Test Call method with HTTP and proxy"""
        # Setup proxy
        self.http_util.proxyHost = "proxy.example.com"
        self.http_util.proxyPort = "8080"
        
        # Setup URL parsing
        mock_uri = Mock()
        mock_uri.hostname = "api.example.com"
        mock_uri.scheme = "http"
        mock_urlparse.return_value = mock_uri
        
        # Setup connection mock
        mock_connection = Mock()
        mock_response = Mock()
        mock_connection.getresponse.return_value = mock_response
        mock_https_connection.return_value = mock_connection
        
        # Call the method
        result = self.http_util.Call(
            method="POST",
            http_uri="http://api.example.com/test",
            data="test data",
            headers={"Content-Type": "application/json"},
            use_https=False
        )
        
        # Verify
        mock_https_connection.assert_called_once_with("proxy.example.com", "8080", timeout=60)
        mock_connection.set_tunnel.assert_called_once_with("api.example.com", 80)
        mock_connection.request.assert_called_once_with(
            method="POST",
            url="http://api.example.com/test",
            body="test data",
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(result, mock_response)

    @patch('HttpUtil.httpclient.HTTPSConnection')
    @patch('HttpUtil.urlparse')
    def test_call_no_proxy_flag(self, mock_urlparse, mock_https_connection):
        """Test Call method with noProxy=True"""
        # Setup proxy (should be ignored)
        self.http_util.proxyHost = "proxy.example.com"
        self.http_util.proxyPort = "8080"
        
        # Setup URL parsing
        mock_uri = Mock()
        mock_uri.hostname = "example.com"
        mock_uri.path = "/test"
        mock_uri.query = None
        mock_urlparse.return_value = mock_uri
        
        # Setup connection mock
        mock_connection = Mock()
        mock_response = Mock()
        mock_connection.getresponse.return_value = mock_response
        mock_https_connection.return_value = mock_connection
        
        # Call the method
        result = self.http_util.Call(
            method="GET",
            http_uri="https://example.com/test",
            data=None,
            headers={},
            use_https=True,
            noProxy=True
        )
        
        # Verify proxy is not used
        mock_https_connection.assert_called_once_with("example.com", timeout=60)
        mock_connection.set_tunnel.assert_not_called()
        self.assertEqual(result, mock_response)

    @patch('HttpUtil.httpclient.HTTPSConnection')
    @patch('HttpUtil.urlparse')
    def test_call_exception_handling(self, mock_urlparse, mock_https_connection):
        """Test Call method exception handling"""
        # Setup URL parsing
        mock_uri = Mock()
        mock_uri.hostname = "example.com"
        mock_uri.path = "/test"
        mock_uri.query = None
        mock_urlparse.return_value = mock_uri
        
        # Setup connection to raise exception
        mock_https_connection.side_effect = Exception("Connection failed")
        
        # Call the method
        result = self.http_util.Call(
            method="GET",
            http_uri="https://example.com/test",
            data=None,
            headers={}
        )
        
        # Verify exception handling
        self.assertIsNone(result)
        self.mock_logger.log.assert_called()
        
        # Check that error message contains expected text
        call_args = self.mock_logger.log.call_args[1] if self.mock_logger.log.call_args[1] else self.mock_logger.log.call_args[0]
        error_msg = call_args[0] if isinstance(call_args, tuple) else call_args.get('msg', str(call_args))
        self.assertIn("Failed to call http with error", error_msg)

    @patch('HttpUtil.httpclient.HTTPSConnection')
    @patch('HttpUtil.urlparse')
    def test_call_getresponse_exception(self, mock_urlparse, mock_https_connection):
        """Test Call method when getresponse raises exception"""
        # Setup URL parsing
        mock_uri = Mock()
        mock_uri.hostname = "example.com"
        mock_uri.path = "/test"
        mock_uri.query = None
        mock_urlparse.return_value = mock_uri
        
        # Setup connection mock that fails on getresponse
        mock_connection = Mock()
        mock_connection.getresponse.side_effect = Exception("Response failed")
        mock_https_connection.return_value = mock_connection
        
        # Call the method
        result = self.http_util.Call(
            method="GET",
            http_uri="https://example.com/test",
            data=None,
            headers={}
        )
        
        # Verify exception handling
        self.assertIsNone(result)
        self.mock_logger.log.assert_called()

    def test_call_query_parameter_handling(self):
        """Test Call method handles query parameters correctly"""
        with patch('HttpUtil.httpclient.HTTPSConnection') as mock_https_connection:
            with patch('HttpUtil.urlparse') as mock_urlparse:
                # Setup URL parsing with query
                mock_uri = Mock()
                mock_uri.hostname = "example.com"
                mock_uri.path = "/api/test"
                mock_uri.query = "param1=value1&param2=value2"
                mock_urlparse.return_value = mock_uri
                
                # Setup connection mock
                mock_connection = Mock()
                mock_response = Mock()
                mock_connection.getresponse.return_value = mock_response
                mock_https_connection.return_value = mock_connection
                
                # Call the method
                result = self.http_util.Call(
                    method="GET",
                    http_uri="https://example.com/api/test?param1=value1&param2=value2",
                    data=None,
                    headers={}
                )
                
                # Verify query is included in URL
                mock_connection.request.assert_called_once_with(
                    method="GET",
                    url="/api/test?param1=value1&param2=value2",
                    body=None,
                    headers={}
                )


if __name__ == '__main__':
    unittest.main()
