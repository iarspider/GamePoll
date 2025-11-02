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

function syncHiddenField() {
    selectedGameIds = [];
    $("#selectedGamesList li").each(function() {
        selectedGameIds.push($(this).data("game-id"));
    });

    $("#selectedIds").val(selectedGameIds.join(","));
}

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

        if (gameItem.closest("#allGamesList").length) {
            gameItem.appendTo("#selectedGamesList");
            $(this).text("Убрать");
        } else {
            gameItem.appendTo("#allGamesList");
            $(this).text("Добавить");
        }

        updateSubmitButtonState();
        syncHiddenField();
    });

    // Reset button click event
    $("#resetBtn").click(function() {
        $("#selectedGamesList li").each(function() {
            $(this).find(".move-btn").text("Добавить");
            $(this).appendTo("#allGamesList");
        });

        updateSubmitButtonState();
        syncHiddenField();
    });

    $("#createPollForm").on("submit", function() {
        syncHiddenField();
    });
}
