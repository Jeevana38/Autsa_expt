document.addEventListener('DOMContentLoaded', () => {
    const video = document.getElementById('video');
    const startButton = document.getElementById('startRecord');
    const stopButton = document.getElementById('stopRecord');
    const recordingTime = document.getElementById('recordingTime');
    let recorder;
    let chunks = [];
    let timer;
    let seconds = 0;

    // Access the user's webcam
    navigator.mediaDevices.getUserMedia({ video: true, audio: true })
    .then(stream => {
        video.srcObject = stream;
        window.stream = stream;
    })
    .catch(err => {
        console.error('Error accessing camera:', err);
        alert('Unable to access camera. Please check permissions.');
    });

    // Start recording
    startButton.addEventListener('click', () => {
        const stream = window.stream;
        recorder = new MediaRecorder(stream);
        chunks = [];

        recorder.ondataavailable = e => {
            if (e.data.size > 0) {
                chunks.push(e.data);
            }
        };

        // 📢 FIX: Set onstop handler immediately when recording starts
        recorder.onstop = async () => {
            const blob = new Blob(chunks, { type: 'video/mp4' });
            const file = new File([blob], "live_video.mp4", { type: "video/mp4" });
           // const blob = new Blob(chunks, { type: 'video/webm' });
            //const file = new File([blob], "live_video.webm", { type: "video/webm" });

            const formData = new FormData();
            formData.append('video', file);

            document.getElementById('loadingSpinner').style.display = "block";
            document.getElementById('result').style.display = "none";

            try {
                const response = await fetch('/process_video', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                document.getElementById('loadingSpinner').style.display = "none";

                Swal.fire({
                    title: 'Success!',
                    text: 'Video processed successfully.',
                    icon: 'success',
                    confirmButtonText: 'OK'
                });

                document.getElementById('result').style.display = "block";
                document.getElementById('emotion').innerText = data.emotion;
                document.getElementById('originalText').innerText = data.original_text;
                document.getElementById('simplifiedText').innerText = data.simplified_text;

                const repliesList = document.getElementById("suggestedReplies");
                repliesList.innerHTML = "";
                data.responses.forEach(res => {
                    const li = document.createElement("li");
                    li.className = "list-group-item";
                    li.textContent = res;
                    repliesList.appendChild(li);
                });

                document.getElementById('audioOutput').src = data.audio_output;
            } catch (error) {
                console.error('Error processing video:', error);
                Swal.fire({
                    title: 'Error!',
                    text: 'Failed to process the video. Try again.',
                    icon: 'error',
                    confirmButtonText: 'OK'
                });
                document.getElementById('loadingSpinner').style.display = "none";
            }
        };

        recorder.start();
        startButton.disabled = true;
        stopButton.disabled = false;
        recordingTime.style.display = "block";
        seconds = 0;
        recordingTime.innerText = "Recording: 0s";

        timer = setInterval(() => {
            seconds++;
            recordingTime.innerText = `Recording: ${seconds}s`;
        }, 1000);
    });

    // Stop recording
    stopButton.addEventListener('click', () => {
        clearInterval(timer);
        recordingTime.style.display = "none";
        startButton.disabled = false;
        stopButton.disabled = true;

        recorder.stop();  // Just stop here, handling happens inside onstop
    });
});
