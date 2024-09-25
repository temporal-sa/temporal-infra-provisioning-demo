function provisionInfra() {
	var selectedScenario = document.getElementById("scenario").value;
	var tfRunID = document.getElementById("tfRunID").value;
	var ephemeralTTL = document.getElementById("ephemeralTTL").valueAsNumber

	// Redirect to provisioninn page with the selected scenario as a query parameter
	window.location.href =
		"/provision_infra?scenario=" + encodeURIComponent(selectedScenario) +
		"&wf_id=" + encodeURIComponent(tfRunID) +
		"&ephemeral_ttl=" + encodeURIComponent(ephemeralTTL);
}

function updateProgress() {
	var urlParams = new URLSearchParams(window.location.search);
	var scenario = urlParams.get("scenario");
	var tfRunID = urlParams.get("wf_id");

	fetch("/get_progress?wf_id=" + encodeURIComponent(tfRunID))
		.then(response => {
			if (response.ok) {
				return response.json();
			} else {
				// If response status is not okay, throw an error
				throw new Error(`Failed to fetch progress. Status: ${response.status}`);
			}
		})
		.then(data => {
			// Update the progress bar
			document.getElementById("errorMessage").innerText = "";
			document.getElementById("progressBar").style.width = data.progress_percent + "%";

			var currentStatusElement = document.getElementById("currentStatus");
			if (currentStatusElement != null) {
				currentStatusElement.innerText = data.status;
			}

			if (data.plan != "") {
				// Display the Terraform plan
				document.getElementById("terraformPlan").innerText = stripAnsi(data.plan);
				document.getElementById("terraformPlanContainer").style.display = "block";
			}

			if (data.status.includes("approval")) {
				// Show the appropriate container based on the scenario
				if (scenario === "human_in_the_loop_signal") {
					document.getElementById("signalContainer").style.display = "block";
				} else if (scenario === "human_in_the_loop_update") {
					document.getElementById("updateContainer").style.display = "block";
				}
			}

			if (data.progress_percent === 100) {
				// Redirect to order confirmation with the tfRunID
				window.location.href =
					"/provisioned?wf_id=" + encodeURIComponent(tfRunID) +
					"&scenario=" + encodeURIComponent(scenario);
			} else {
				// Continue updating progress every second
				setTimeout(updateProgress, 1000);
			}
		})
		.catch(error => {
			// Log the detailed error message to the console
			console.error("Error fetching progress:", error.message);

			// Display the error message in the web browser
			document.getElementById("errorMessage").innerText = error.message;

			// Handle the error by showing a red status bar
			document.getElementById("progressBar").style.backgroundColor = "red";
		});
}

function signal(decision) {
	// Get the tfRunID from the URL query parameters
	var urlParams = new URLSearchParams(window.location.search);
	var tfRunID = urlParams.get("wf_id");

	// Perform AJAX request to the server for signaling
	fetch("/signal?wf_id=" + encodeURIComponent(tfRunID), {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			decision: decision
		})
	})
		.then(response => {
			if (response.ok) {
				console.log("Signal sent successfully");
			} else {
				console.error("Failed to send signal");

				// Get the signalResult element
				var signalResultElement = document.getElementById("errorMessage");

				// Update the display with the result
				signalResultElement.innerText = "Signal sent failed";
			}
		})
		.catch(error => {
			console.error("Error during signal:", error.message);
		});
}

function update(decision) {
	// Get the tfRunID from the URL query parameters
	var urlParams = new URLSearchParams(window.location.search);
	var tfRunID = urlParams.get("wf_id");
	var reason = document.getElementById("reason").value;
	var updateResultElement = document.getElementById("updateResult");
	updateResultElement.style.display = "none";


	// Perform AJAX request to the server for updating
	fetch("/update?wf_id=" + encodeURIComponent(tfRunID), {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			decision: decision,
			reason: reason
		})
	})
	.then(response => {
		if (response.status !== 200) {
			console.error("Failed to send update");
			updateResultElement.style.display = "block";
			updateResultElement.innerText = "Update sent failed, enter a reason and try again."
		}
	})
	.catch(error => {
		console.error("Error during update:", error.message);
	});
}

function handleScenarioChange(event) {
	var scenario = event.target.value;
	console.log(scenario);
	if (scenario === "ephemeral") {
		document.getElementById("ephemeralContainer").style.display = "block";
	} else {
		document.getElementById("ephemeralContainer").style.display = "none";
	}
}

function reloadMainPage() {
	// Redirect to the main page
	window.location.href = "/";
}

function stripAnsi(text) {
  // This regex matches ANSI escape sequences
  const ansiRegex = /\x1b\[[0-9;]*m/g;

  // Replace the ANSI escape codes with an empty string
  return text.replace(ansiRegex, "");
}
