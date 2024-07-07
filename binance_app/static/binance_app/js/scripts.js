function toggleDates() {
    var historyDropdown = document.getElementById("history-dropdown");
    var startDateDiv = document.getElementById("start-date");
    var endDateDiv = document.getElementById("end-date");

    if (historyDropdown.value === "non-history") {
        startDateDiv.style.display = "none";
        endDateDiv.style.display = "none";
    } else {
        startDateDiv.style.display = "block";
        endDateDiv.style.display = "block";
    }
}

function populateSymbolDropdown(symbols) {
var symbolDropdown = document.getElementById("symbol");

// Clear existing options (if any)
symbolDropdown.innerHTML = '';

// Add default option
var defaultOption = document.createElement("option");
defaultOption.text = 'Select Symbol';
defaultOption.value = '';
symbolDropdown.appendChild(defaultOption);

// Add symbols as options
symbols.forEach(function(symbol) {
var option = document.createElement("option");
option.text = symbol;
option.value = symbol;
symbolDropdown.appendChild(option);
});
}

// Fetch symbols from Django backend
async function fetchSymbols() {
try {
const response = await fetch('/get_binance_symbols/');
if (!response.ok) {
    throw new Error('Failed to fetch symbols');
}
const data = await response.json();
if (data.symbols) {
    populateSymbolDropdown(data.symbols);
} else {
    console.error('Error fetching symbols:', data.error);
}
} catch (error) {
console.error('Error fetching symbols:', error);
}
}

// Call function to fetch symbols and populate dropdown when page loads
document.addEventListener('DOMContentLoaded', function() {
fetchSymbols();
});

// Optionally, if the endpoint dropdown changes dynamically
function toggleSymbolDropdown() {
var endpointDropdown = document.getElementById("type-dropdown");
var symbolDropdown = document.getElementById("symbol-dropdown");

if (endpointDropdown.value === "recent_trades") {
symbolDropdown.style.display = "block";
fetchSymbols();  // Call function to fetch symbols
} else {
symbolDropdown.style.display = "none";
}
}