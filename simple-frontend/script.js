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

            // Generate and print the receipt
            printReceipt(result.queue_number, type, status);
        } else {
            const error = await response.json();
            document.getElementById("manualInputResponse").innerText = `Error: ${error.detail}`;
        }
    } catch (error) {
        console.error("Error adding queue:", error);
        document.getElementById("manualInputResponse").innerText = "Error adding queue.";
    }
});

// Function to print the receipt
function printReceipt(queueNumber, type, status) {
    const receiptText = `
        MyBank Express
        ----------------------
        Queue Number: ${queueNumber}
        Transaction: ${type}
        Status: ${status}
        Date: ${new Date().toLocaleString()}
        ----------------------
        Please wait for your turn.
        Thank you!
    `;

    console.log("Printing receipt:");
    console.log(receiptText);

    // Send the receipt to the printer
    const rawData = receiptText;
    const hPrinter = window.open("", "_blank");
    hPrinter.document.write(`<pre>${rawData}</pre>`);
    hPrinter.document.close();
    hPrinter.print();
    hPrinter.close();
}

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



async function loadArchivedPage(page = 1) {
    try {
        const response = await fetch(`http://127.0.0.1:8000/queue/archived?page=${page}&page_size=10`);
        const archivedQueues = await response.json();

        const table = document.getElementById("archivedQueueTable");
        if (archivedQueues.length === 0) {
            table.innerHTML = `
                <tr>
                    <td colspan="3" style="text-align: center;">No archived queues available</td>
                </tr>
            `;
        } else {
            table.innerHTML = archivedQueues.map(queue => `
                <tr>
                    <td>${queue.queue_number}</td>
                    <td>${queue.type}</td>
                    <td>${queue.status}</td>
                    <td>${queue.date}</td>
                </tr>
            `).join("");
        }
    } catch (error) {
        console.error("Error loading archived queues:", error);
    }
}