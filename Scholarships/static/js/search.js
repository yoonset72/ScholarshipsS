document.addEventListener("DOMContentLoaded", () => {
    const programInput = document.getElementById("program-search");
    const suggestionsContainer = document.getElementById("suggestions");

    // Load the JSON data
    fetch('json/programmes.json')
        .then(response => response.json())
        .then(data => {
            const programs = [];
            // Flatten the programs from the data into a single array
            for (const country in data) {
                programs.push(...data[country]);
            }

            // Add input event listener for autocomplete
            programInput.addEventListener("input", function() {
                const value = this.value.toLowerCase();
                suggestionsContainer.innerHTML = ''; // Clear previous suggestions

                if (value) {
                    const filteredPrograms = programs.filter(program => 
                        program.toLowerCase().includes(value)
                    );

                    filteredPrograms.forEach(program => {
                        const suggestionItem = document.createElement("div");
                        suggestionItem.classList.add("suggestion-item");
                        suggestionItem.textContent = program;
                        suggestionItem.addEventListener("click", function() {
                            programInput.value = program; // Set input value to clicked suggestion
                            suggestionsContainer.innerHTML = ''; // Clear suggestions
                        });
                        suggestionsContainer.appendChild(suggestionItem);
                    });
                }
            });
        })
        .catch(error => console.error('Error loading JSON:', error));
});
