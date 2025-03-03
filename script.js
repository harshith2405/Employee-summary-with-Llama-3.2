document
  .getElementById("employeeForm")
  .addEventListener("submit", function (e) {
    e.preventDefault();

    // Get the query value
    let prompt = document.getElementById("query").value;
    let employee_ids = document.getElementById("ids").value; // Assume multiple IDs are comma-separated

    // Check if prompt is entered
    if (!prompt) {
      alert("Please enter a prompt.");
      return;
    }
    if (!employee_ids) {
      alert("Please enter Employee IDs.");
      return;
    }

    // Split the employee_ids string into an array
    let idsArray = employee_ids.split(",").map((id) => id.trim());

    // Check if all IDs are numeric
    if (idsArray.some((id) => isNaN(id))) {
      alert("Please enter valid numeric Employee IDs.");
      return;
    }

    // Construct the query with the prompt and employee IDs
    let query = `${prompt}&ids=${idsArray.join(",")}`;

    // Fetch employee info from the backend
    fetch(`http://127.0.0.1:8000/employee/${query}`)
      .then((response) => response.json())
      .then((data) => {
        console.log("API Response:", data); // Debugging response
        document.getElementById("summaries").textContent = data.summaries;
        document.getElementById("details").textContent = JSON.stringify(
          data.details,
          null,
          2
        ); // Format details for better readability
      })
      .catch((error) => {
        alert("Error fetching employee details.");
        console.error("Error:", error); // Debugging
      });
  });
