const API_URL = 'http://127.0.0.1:8000';

// Function to display a result message in the specified container
function displayResult(message, containerId) {
  const resultContainer = document.getElementById(containerId);
  const resultElement = document.createElement('p');
  resultElement.textContent = message;
  resultContainer.appendChild(resultElement);
}

// Function to send a new music to the API
async function submitMusic(event) {
  event.preventDefault();

  const musicFile = document.getElementById('musicFile').files[0];

  const formData = new FormData();
  formData.append('file', musicFile);

  try {
    const response = await fetch(API_URL + '/music', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();
    displayResult('New music submitted successfully!', 'submitResultContainer');
    displayResult('Music ID: ' + data.music_id, 'submitResultContainer');
    const tracks = data.tracks.map((track) => {
      return {
        'track_id': track.track_id,
        'name': track.name
      };
    });

    displayResult('Tracks:', 'submitResultContainer');
    displayResult(JSON.stringify(tracks, null, 2), 'submitResultContainer');
  } catch (error) {
    console.error('Error submitting music:', error);
  }
}

// Function to list all music
async function listMusic(event) {
  event.preventDefault();

  try {
    const response = await fetch(API_URL + '/music');
    const data = await response.json();
    displayResult('List of music:', 'listMusicResultContainer');
    data.forEach((music) => {
      displayResult('Music ID: ' + music.music_id, 'listMusicResultContainer');
      const tracks = music.tracks.map((track) => {
        return {
          'track_id': track.track_id,
          'name': track.name
        };
      });
      displayResult(JSON.stringify(tracks, null, 2), 'listMusicResultContainer');

      displayResult('--------------------------', 'listMusicResultContainer');
    });
  } catch (error) {
    console.error('Error listing music:', error);
  }
}

// Function to process a music
async function processMusic(event) {
  event.preventDefault();

  const specificMusicId = document.getElementById('specificMusicId').value;
  const instrumentIds = document.getElementById('instrumentIds').value.split(',');

  try {
    const response = await fetch(API_URL + `/music/${specificMusicId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        tracks: instrumentIds.map(Number) // Convert instrumentIds to an array of numbers
      })
    });

    const data = await response.json();
    displayResult(JSON.stringify(data), 'processMusicResultContainer');
    ;
  } catch (error) {
    console.error('Error processing music:', error);
  }
}

// Function to fetch the status of a specific music
async function fetchMusicStatus(event) {
  event.preventDefault();

  const specificMusicId = document.getElementById('specificMusicId').value;

  try {
    const response = await fetch(API_URL + `/music/${specificMusicId}`);
    const data = await response.json();
    displayResult(JSON.stringify(data), 'musicStatusResultContainer');
    if (data.processing_state === 100) {
      const downloadResponse = await fetch(API_URL + `/download/${specificMusicId}`, {
        method: 'GET'
      });

      if (!downloadResponse.ok) {
        throw new Error('Error in download request');
      }
      displayResult(`Download link generated`, 'musicStatusResultContainer');

      displayResult(`Final file URL: ${downloadResponse.url}`, 'musicStatusResultContainer');
      // Create a download button
      const downloadButton = document.createElement('a');
      downloadButton.href = downloadResponse.url; 
      downloadButton.download = '';
      downloadButton.textContent = 'Download final file';
      downloadButton.className = 'btn btn-primary';

      document.getElementById('musicStatusResultContainer').appendChild(downloadButton);
    }
  } catch (error) {
    console.error('Error fetching music status:', error);
  }
}

// Function to list all jobs
async function listJobs(event) {
    event.preventDefault();

    try {
        const response = await fetch(API_URL + '/job');
        const data = await response.json();
        displayResult('List of jobs:', 'listJobsResultContainer');
        displayResult(JSON.stringify(data, null, 2), 'listJobsResultContainer');
    } catch (error) {
        console.error('Error listing jobs:', error);
    }
}

// Function to fetch information about a specific job
async function fetchJob(event) {
    event.preventDefault();

    const specificJobId = document.getElementById('specificJobId').value;

    try {
        const response = await fetch(API_URL + `/job/${specificJobId}`);
        const data = await response.json();
        displayResult('Job information:', 'fetchJobResultContainer');
        displayResult(JSON.stringify(data, null, 2), 'fetchJobResultContainer');
    } catch (error) {
        console.error('Error fetching job information:', error);
    }
}

// Function to reset the system
async function resetSystem(event) {
    event.preventDefault();

    try {
        await fetch(API_URL + '/reset', {
            method: 'POST'
        });
        displayResult('System reset successfully!', 'resetSystemResultContainer');
    } catch (error) {
        console.error('Error resetting the system:', error);
    }
}

// Event listeners for each form
document.getElementById('uploadForm').addEventListener('submit', submitMusic);
document.getElementById('listMusicForm').addEventListener('submit', listMusic);
document.getElementById('musicForm').addEventListener('submit', processMusic);
document.getElementById('fetchMusicStatusForm').addEventListener('submit', fetchMusicStatus);
document.getElementById('listJobsForm').addEventListener('submit', listJobs);
document.getElementById('jobForm').addEventListener('submit', fetchJob);
document.getElementById('resetForm').addEventListener('submit', resetSystem);
