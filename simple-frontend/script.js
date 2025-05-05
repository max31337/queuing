function showPage(pageId) {
    document.querySelectorAll("section").forEach(section => {
        section.classList.remove("active");
    });
    document.getElementById(pageId).classList.add("active");

    // If navigating to the Archived List, load the first page of archived queues
    if (pageId === "archivedList") {
        loadArchivedPage(1); // Load the first page of archived queues
    }
}

function openQueueList() {
    window.open("./queue-list.html", "_blank");
}

let currentQueueId = null;
let nextQueueNumber = null;
let skippedQueues = [];

async function loadQueueNumbers() {
    try {
        const response = await fetch("http://127.0.0.1:8000/queue/numbers");
        const data = await response.json();
        console.log(data); // Log the API response

        if (data.waiting.length > 0) {
            const currentQueue = data.waiting[0];
            const queueDetailsResponse = await fetch(`http://127.0.0.1:8000/queue?queue_number=${currentQueue}`);
            const queueDetails = await queueDetailsResponse.json();

            if (queueDetails.length > 0) {
                currentQueueId = queueDetails[0].id;
                document.getElementById("currentNumber").innerText = `Serving: ${queueDetails[0].queue_number}`;
                document.getElementById("queueId").value = currentQueueId;
            }
        } else {
            document.getElementById("currentNumber").innerText = "Serving: No queues";
            document.getElementById("queueId").value = "";
            currentQueueId = null;
        }

        if (data.waiting.length > 1) {
            nextQueueNumber = data.waiting[1];
            document.getElementById("nextNumber").innerText = `Next: ${nextQueueNumber}`;
        } else {
            document.getElementById("nextNumber").innerText = "Next: No queues";
            nextQueueNumber = null;
        }

        loadProcessingQueue(data.processing);
        loadSkippedQueues();
    } catch (error) {
        console.error("Error loading queue numbers:", error);
    }
}

function loadProcessingQueue(processingQueue) {
    const table = document.getElementById("processingQueueTable");

    if (processingQueue.length === 0) {
        table.innerHTML = `
            <tr>
                <td colspan="3" style="text-align: center;">No processing queues available</td>
            </tr>
        `;
    } else {
        table.innerHTML = processingQueue.map(queue => `
            <tr>
                <td>${queue}</td>
                <td>${queue.split(/(\d+)/)[0]}</td>
                <td><button onclick="markAsDone('${queue}')">Mark as Done</button></td>
            </tr>
        `).join("");
    }
}

async function markAsDone(queueNumber) {
    const queueDetailsResponse = await fetch(`http://127.0.0.1:8000/queue?queue_number=${queueNumber}`);
    const queueDetails = await queueDetailsResponse.json();

    if (queueDetails.length > 0) {
        const queueId = queueDetails[0].id;
        const data = { status: "done" };

        const response = await fetch(`http://127.0.0.1:8000/queue/${queueId}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            document.getElementById("counterResponse").innerText = `Queue ${queueNumber} marked as done.`;
            setTimeout(() => {
                document.getElementById("counterResponse").innerText = "";
            }, 3000);

            saveLastServed(queueNumber);
            loadQueueNumbers();
        } else {
            const error = await response.json();
            document.getElementById("counterResponse").innerText = `Error: ${error.detail}`;
        }
    }
}

async function markAsWaiting(queueId) {
    try {
        const response = await fetch(`http://127.0.0.1:8000/queue/${queueId}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: "waiting" })
        });

        if (response.ok) {
            document.getElementById("manualInputResponse").innerText = "Queue marked as waiting.";
            setTimeout(() => {
                document.getElementById("manualInputResponse").innerText = "";
            }, 3000);

            loadSkippedQueues(); // Refresh the skipped queues
            loadQueueNumbers(); // Refresh the queue numbers
        } else {
            const error = await response.json();
            document.getElementById("manualInputResponse").innerText = `Error: ${error.detail}`;
        }
    } catch (error) {
        console.error("Error marking queue as waiting:", error);
    }
}

async function skipCurrentQueue() {
    if (!currentQueueId) {
        document.getElementById("counterResponse").innerText = "Error: No queue to skip.";
        setTimeout(() => {
            document.getElementById("counterResponse").innerText = "";
        }, 3000);
        return;
    }

    const response = await fetch(`http://127.0.0.1:8000/queue/${currentQueueId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "skipped" })
    });

    if (response.ok) {
        await loadQueueNumbers();
    } else {
        const error = await response.json();
        document.getElementById("counterResponse").innerText = `Error: ${error.detail}`;
    }
}

function saveLastServed(queueNumber) {
    localStorage.setItem("lastServed", queueNumber);
    document.getElementById("lastServed").innerText = `Last Served: ${queueNumber}`;
}

async function loadSkippedQueues() {
    try {
        const response = await fetch("http://127.0.0.1:8000/queue/skipped");
        const skippedQueues = await response.json();

        // Display in the "Skipped Queues" section
        const skippedQueueList = document.getElementById("skippedQueueList");
        if (skippedQueues.length === 0) {
            skippedQueueList.innerHTML = `<li>No skipped queues available</li>`;
        } else {
            skippedQueueList.innerHTML = skippedQueues
                .map(queue => `<li>${queue.queue_number}</li>`)
                .join("");
        }

        // Display in the "Update Skipped Queues" section
        const skippedQueueUpdateList = document.getElementById("skippedQueueUpdateList");
        if (skippedQueues.length === 0) {
            skippedQueueUpdateList.innerHTML = `<li>No skipped queues available</li>`;
        } else {
            skippedQueueUpdateList.innerHTML = skippedQueues
                .map(queue => `
                    <li>
                        ${queue.queue_number}
                        <button onclick="markAsWaiting('${queue.id}')">Mark as Waiting</button>
                    </li>
                `)
                .join("");
        }
    } catch (error) {
        console.error("Error loading skipped queues:", error);
    }
}

document.getElementById("counterForm").addEventListener("submit", async function (event) {
    event.preventDefault();

    if (!currentQueueId) {
        document.getElementById("counterResponse").innerText = "Error: No queue to update.";
        return;
    }

    const newStatus = document.getElementById("newStatus").value;
    const data = { status: newStatus };

    const response = await fetch(`http://127.0.0.1:8000/queue/${currentQueueId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });


    if (response.ok) {
        const result = await response.json();
        document.getElementById("counterResponse").innerText = `Queue updated successfully: ${result.queue_number}`;
        setTimeout(() => {
            document.getElementById("counterResponse").innerText = "";
        }, 3000);

        saveLastServed(result.queue_number);
        loadQueueNumbers();
    } else {
        const error = await response.json();
        document.getElementById("counterResponse").innerText = `Error: ${error.detail}`;
    }
});

document.getElementById("queueForm").addEventListener("submit", async function (event) {
    event.preventDefault();

    const type = document.getElementById("type").value;
    const status = document.getElementById("status").value;

    try {
        // Save the queue to the database
        const response = await fetch("http://127.0.0.1:8000/manual-input", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ type, status })
        });

        if (response.ok) {
            const result = await response.json();
            document.getElementById("manualInputResponse").innerText = `Queue added successfully: ${result.queue_number}`;
            setTimeout(() => {
                document.getElementById("manualInputResponse").innerText = "";
            }, 3000);

        } else {
            const error = await response.json();
            document.getElementById("manualInputResponse").innerText = `Error: ${error.detail}`;
        }
    } catch (error) {
        console.error("Error adding queue:", error);
        document.getElementById("manualInputResponse").innerText = "Error adding queue.";
    }
});


loadQueueNumbers();
loadSkippedQueues();

// Run loadQueueNumbers every second
setInterval(loadQueueNumbers, 1500);

async function loadActiveQueue() {
    const response = await fetch("http://127.0.0.1:8000/queue/active");
    const data = await response.json();
    const table = document.getElementById("activeQueueTable");
    table.innerHTML = data.map(queue => `
        <tr>
            <td>${queue.queue_number}</td>
            <td>${queue.type}</td>
            
            <td>${queue.status}</td>
        </tr>
    `).join("");
}

// Refresh the queue list every 2 seconds
setInterval(loadActiveQueue, 2000);
loadActiveQueue();

let currentArchivedPage = 1; // Track the current page
let totalArchivedPages = 1; // Track the total number of pages

async function loadArchivedPage(page = 1) {
    try {
        const response = await fetch(`http://127.0.0.1:8000/queue/archived?page=${page}&page_size=10`);
        const archivedQueues = await response.json();

        const table = document.getElementById("archivedQueueTable");
        if (archivedQueues.length === 0) {
            table.innerHTML = `
                <tr>
                    <td colspan="4" style="text-align: center;">No archived queues available</td>
                </tr>
            `;
        } else {
            table.innerHTML = archivedQueues.map(queue => {
                // Format the timestamp
                const timestamp = new Date(queue.timestamp);
                const formattedDate = timestamp.toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric'
                });
                const formattedTime = timestamp.toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit'
                });
                
                return `
                <tr>
                    <td>${queue.queue_number}</td>
                    <td>${queue.type}</td>
                    <td>${queue.status}</td>
                    <td>${formattedDate} ${formattedTime}</td>
                </tr>
                `;
            }).join("");
        }

        // Update the current page and total pages
        currentArchivedPage = page;

        // Fetch the total number of archived queues to calculate total pages
        const countResponse = await fetch("http://127.0.0.1:8000/queue/archived/count");
        const totalArchivedCount = await countResponse.json();
        totalArchivedPages = Math.ceil(totalArchivedCount / 10);

        // Enable/disable the Previous and Next buttons
        document.getElementById("prevButton").disabled = currentArchivedPage === 1;
        document.getElementById("nextButton").disabled = currentArchivedPage === totalArchivedPages;
    } catch (error) {
        console.error("Error loading archived queues:", error);
    }
}

function goToPreviousPage() {
    if (currentArchivedPage > 1) {
        loadArchivedPage(currentArchivedPage - 1);
    }
}

function goToNextPage() {
    if (currentArchivedPage < totalArchivedPages) {
        loadArchivedPage(currentArchivedPage + 1);
    }
}