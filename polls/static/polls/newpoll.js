// Function to update the state of the Submit button
function updateSubmitButtonState() {
    const numSelectedGames = $("#selectedGamesList li").length;
    $("#submitBtn").prop("disabled", numSelectedGames <= 2);
}

function toDatetimeLocal(date) {
    const
        ten = function(i) {
            return (i < 10 ? '0' : '') + i;
        },
        YYYY = date.getFullYear(),
        MM = ten(date.getMonth() + 1),
        DD = ten(date.getDate()),
        HH = ten(date.getHours()),
        II = ten(date.getMinutes());
    return YYYY + '-' + MM + '-' + DD + 'T' +
        HH + ':' + II;
}

function toISOTime(input) {
    const elem_str = document.getElementById(input).value;
    return (new Date(elem_str)).toISOString();
}

let selectedGameIds = [];

function init_new_poll() {
    $("#submitBtn").prop("disabled", true);
    // Set default values for start_date and end_date adjusted for the client's time zone
    const currentDate = new Date();
    $("#start_date").val(toDatetimeLocal(currentDate));

    const defaultEndDate = new Date();
    defaultEndDate.setDate(defaultEndDate.getDate() + 1);
    $("#end_date").val(toDatetimeLocal(defaultEndDate));

    // Enable sorting for connected lists
    $(".connectedSortable").sortable({
        connectWith: ".connectedSortable",
        update: function(event, ui) {
            // Update the state of the Submit button when the list is updated
            updateSubmitButtonState();
        }
    });

    // Move button click event
    $(".move-btn").click(function() {
        const gameItem = $(this).parent();
        const gameId = gameItem.data("game-id");

        // Add list
        if (gameItem.closest("#allGamesList").length) {
            gameItem.appendTo("#selectedGamesList");
            $(this).text("Убрать");
            selectedGameIds.push(gameId);
        } else {
            // Del list
            gameItem.appendTo("#allGamesList");
            $(this).text("Добавить");
            const index = selectedGameIds.indexOf(gameId);
            selectedGameIds.splice(index, 1);
        }

        // Update the state of the Submit button when a game is moved
        updateSubmitButtonState();
    });

    // Reset button click event
    $("#resetBtn").click(function() {
        $("#selectedGamesList li").appendTo("#allGamesList");
        $("#selectedGamesList .move-btn").text("Add");

        // Update the state of the Submit button when games are reset
        updateSubmitButtonState();
    });

    // Submit button click event
    $("#createPollForm").submit(function(event) {
        event.preventDefault();
        // Get the API endpoint URL from the form's action attribute
        const apiEndpoint = $(event.target).attr('action');

        const data = {
            "start_date": toISOTime("start_date"),
            "end_date": toISOTime("end_date"),
            "selectedIds": selectedGameIds,
            "anonymous": $("#anonymous").prop("checked"),
            "title": $("#title")[0].value,
        };

        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const jsonData = JSON.stringify(data);
        // Make an AJAX request with the JSON data
        fetch(apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken,
                },
                body: jsonData,
                mode: 'same-origin'
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.text(); // Assuming the API returns a plain text URL
            })
            .then(url => {
                // Navigate to the URL received from the API response
                window.location.href = url;
            })
            .catch(error => {
                // Handle the error
                console.error(error);
            });
    })
}
