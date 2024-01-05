function shuffle_click() {
    $(".card").not(".excluded").sort(function () {
        return Math.random() - 0.5;
    }).appendTo("#sortable-list");
}

function reset_click() {
    const cards = Array.from($("#sortable-list .card"));

    // Sort cards by Steam ID
    cards.sort(function (a, b) {
        const steamIdA = parseInt($(a).data("stream-id"));
        const steamIdB = parseInt($(b).data("stream-id"));
        return steamIdA - steamIdB;
    });

    // Append sorted cards to the list
    $("#sortable-list").html("");
    cards.forEach(function (card) {
        $("#sortable-list").append(card);
    });

    // Mark all games as included
    $("#sortable-list input[type='checkbox']").prop("checked", true);
}

function cast_click(event) {
    event.preventDefault();
    const apiEndpoint = $(event.target).attr('action');
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    const voteData = {
        game_order: $("#sortable-list .card").map(function () {
            return $(this).data("stream-id");
        }).get(),
        game_states: {}
    };

    $(".card").each(function () {
        const streamId = $(this).data("stream-id");
        voteData.game_states[streamId] = $(this).find("input[type='checkbox']").prop("checked");
    });

    voteData.owl_checkbox = $("input[name='owl_checkbox']").prop("checked");
    voteData.cheese_checkbox = $("input[name='cheese_checkbox']").prop("checked");
    voteData.bee_checkbox = $("input[name='bee_checkbox']").prop("checked");

    fetch(apiEndpoint, {
        method: "POST",
        headers: {
            "Content-Type": "application/json; charset=utf-8",
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify(voteData),
        mode: 'same-origin'
    })
        .then(response => {
            if (!response.ok) {
                throw new Error("Network response was not ok");
            }
            if (response.redirected) {
                // Perform the redirect
                window.location.href = response.url;
            } else {
                // Handle other successful responses
                throw new Error();
            }
        })
        .catch(error => {
            console.error("Error casting vote:", error);
        });
}

function exclude_click() {
    const cardDiv = $(this).closest('.card');
    cardDiv.toggleClass('excluded', !$(this).prop('checked'));
}

// Update button status based on item position
function updateButtonStatus() {
    $(".move-to-top, .move-up, .move-down, .move-to-bottom").prop("disabled", false);

    $(".move-to-top:first, .move-up:first").prop("disabled", true);
    $(".move-down:last, .move-to-bottom:last").prop("disabled", true);
}

// Function to handle moving an item up
function move_up_click() {
    const currentListItem = $(this).closest("li");
    currentListItem.insertBefore(currentListItem.prev());
    updateButtonStatus();
}

// Function to handle moving an item down
function move_down_click() {
    const currentListItem = $(this).closest("li");
    currentListItem.insertAfter(currentListItem.next());
    updateButtonStatus();
}

// Function to handle moving an item to the top
function move_to_top_click() {
    const currentListItem = $(this).closest("li");
    currentListItem.prependTo("#sortable-list");
    updateButtonStatus();
}

// Function to handle moving an item to the bottom
function move_to_bottom_click() {
    const currentListItem = $(this).closest("li");
    currentListItem.appendTo("#sortable-list");
    updateButtonStatus();
}

function init_addvote() {
    // Make the game list reorderable
    $("#sortable-list").sortable();

    // Shuffle button functionality
    $("#shuffleButton").click(shuffle_click);

    // Form submission functionality
    $("#voteForm").submit(cast_click);

    // Reset button functionality
    $("#resetButton").click(reset_click);

    // Exclusion checkboxes functionallity
    $('input[name^="game_"]').click(exclude_click);

    // Move buttons functionality
    $(".move-up").click(move_up_click);
    $(".move-down").click(move_down_click);
    $(".move-to-top").click(move_to_top_click);
    $(".move-to-bottom").click(move_to_bottom_click);
}