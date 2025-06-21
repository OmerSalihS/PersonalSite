document.addEventListener("DOMContentLoaded", () => {
    console.log("Piano script loaded!"); // Debugging Check

    // Create audio context for better sound generation
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    
    // Piano key frequencies (in Hz)
    const frequencies = {
        65: 261.63,  // A -> C4
        87: 277.18,  // W -> C#4
        83: 293.66,  // S -> D4
        69: 311.13,  // E -> D#4
        68: 329.63,  // D -> E4
        70: 349.23,  // F -> F4
        84: 369.99,  // T -> F#4
        71: 392.00,  // G -> G4
        89: 415.30,  // Y -> G#4
        72: 440.00,  // H -> A4
        85: 466.16,  // U -> A#4
        74: 493.88,  // J -> B4
        75: 523.25,  // K -> C5
        79: 554.37,  // O -> C#5
        76: 587.33,  // L -> D5
        80: 622.25,  // P -> D#5
        186: 659.25  // ; -> E5
    };

    // Function to play a tone
    function playTone(frequency, duration = 0.5) {
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.setValueAtTime(frequency, audioContext.currentTime);
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + duration);
    }

    // Play sound when a key is pressed
    document.addEventListener("keydown", function(event) {
        // Prevent repeat events when key is held down
        if (event.repeat) return;
        
        console.log(`Key pressed: ${event.keyCode}`); // Debugging
        let key = document.querySelector(`[data-key="${event.keyCode}"]`);
        
        if (key && frequencies[event.keyCode]) {
            // Resume audio context if needed (browser security requirement)
            if (audioContext.state === 'suspended') {
                audioContext.resume();
            }
            
            playTone(frequencies[event.keyCode]);

            // Apply visual effect
            key.classList.add("pressed");
        }
    });

    // Remove visual effect when key is released
    document.addEventListener("keyup", function(event) {
        let key = document.querySelector(`[data-key="${event.keyCode}"]`);
        if (key) {
            key.classList.remove("pressed");
        }
    });

    // Add click functionality for mouse interaction
    document.querySelectorAll(".piano div").forEach(key => {
        const keyCode = parseInt(key.getAttribute('data-key'));
        
        key.addEventListener("click", () => {
            if (frequencies[keyCode]) {
                // Resume audio context if needed
                if (audioContext.state === 'suspended') {
                    audioContext.resume();
                }
                
                playTone(frequencies[keyCode]);
                
                // Apply visual effect
                key.classList.add("pressed");
                setTimeout(() => key.classList.remove("pressed"), 200);
            }
        });

        // Show letter on hover
        key.addEventListener("mouseenter", () => {
            const span = key.querySelector("span");
            if (span) span.style.display = "block";
        });
        
        key.addEventListener("mouseleave", () => {
            const span = key.querySelector("span");
            if (span) span.style.display = "none";
        });
    });

    console.log("Key listeners added!"); // Debugging Check
});
