/**
 * Test script to verify the connection to the deployed API
 * Run with: node test-api-connection.js
 */

const https = require('https');

// The deployed API URL
const API_URL = 'https://fastapi-5aw3.onrender.com';

console.log(`Testing connection to ${API_URL}/health...`);

// Make a request to the health endpoint
https.get(`${API_URL}/health`, (res) => {
  const { statusCode } = res;
  const contentType = res.headers['content-type'];

  let error;
  if (statusCode !== 200) {
    error = new Error(`Request Failed.\nStatus Code: ${statusCode}`);
  } else if (!/^application\/json/.test(contentType)) {
    error = new Error(`Invalid content-type.\nExpected application/json but received ${contentType}`);
  }
  
  if (error) {
    console.error(error.message);
    // Consume response data to free up memory
    res.resume();
    return;
  }

  res.setEncoding('utf8');
  let rawData = '';
  res.on('data', (chunk) => { rawData += chunk; });
  res.on('end', () => {
    try {
      const parsedData = JSON.parse(rawData);
      console.log('Connection successful!');
      console.log('API Response:', parsedData);
    } catch (e) {
      console.error(`Error parsing JSON response: ${e.message}`);
    }
  });
}).on('error', (e) => {
  console.error(`Connection error: ${e.message}`);
});

// Test the search endpoint
console.log(`Testing search endpoint at ${API_URL}/search...`);

const searchData = JSON.stringify({
  query: 'adventure',
  limit: 1
});

const searchOptions = {
  hostname: 'fastapi-5aw3.onrender.com',
  path: '/search',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(searchData)
  }
};

const searchReq = https.request(searchOptions, (res) => {
  const { statusCode } = res;
  let rawData = '';
  
  res.setEncoding('utf8');
  res.on('data', (chunk) => { rawData += chunk; });
  res.on('end', () => {
    console.log(`Search endpoint status code: ${statusCode}`);
    if (statusCode === 200) {
      try {
        const parsedData = JSON.parse(rawData);
        console.log('Search successful!');
        console.log(`Found ${parsedData.items ? parsedData.items.length : 'unknown'} results`);
        if (parsedData.items && parsedData.items.length > 0) {
          console.log('First result:', parsedData.items[0].name);
        }
      } catch (e) {
        console.error(`Error parsing search response: ${e.message}`);
      }
    } else {
      console.error(`Search request failed with status code: ${statusCode}`);
      console.error('Response body:', rawData);
    }
  });
});

searchReq.on('error', (e) => {
  console.error(`Search request error: ${e.message}`);
});

searchReq.write(searchData);
searchReq.end(); 