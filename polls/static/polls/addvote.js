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
        }).get(), game_states: {}
    };

    $(".card").each(function () {
        const streamId = $(this).data("stream-id");
        voteData.game_states[streamId] = $(this).find("input[type='checkbox']").prop("checked");
    });

    voteData.owl_checkbox = $("input[name='owl_checkbox']").prop("checked");
    voteData.cheese_checkbox = $("input[name='cheese_checkbox']").prop("checked");
    voteData.bee_checkbox = $("input[name='bee_checkbox']").prop("checked");

    fetch(apiEndpoint, {
        method: "POST", headers: {
            "Content-Type": "application/json; charset=utf-8", 'X-CSRFToken': csrftoken,
        }, body: JSON.stringify(voteData), mode: 'same-origin'
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

function init_addvote() {
    // Make the game list reorderable
    $("#sortable-list").sortable({handle: ".handle"})

    // Shuffle button functionality
    $("#shuffleButton").click(shuffle_click);

    // Form submission functionality
    $("#voteForm").submit(cast_click);

    // Reset button functionality
    $("#resetButton").click(reset_click);

    // Exclusion checkboxes functionallity
    $('input[name^="game_"]').click(exclude_click);
    const isTouchDevice = window.matchMedia("(pointer: coarse)").matches;
    // Show/hide buttons based on touch support
    if (isTouchDevice) {
        $("h1")[0].innerHTML += " - Touch"
        $(".btn-move-up, .btn-move-down, .btn-move-top, .btn-move-bottom").show();
        // $(".handle").hide();
    } else {
        $("h1")[0].innerHTML += " - No touch    "
        $(".btn-move-up, .btn-move-down, .btn-move-top, .btn-move-bottom").hide();
        // $(".handle").show();
    }

    // Game move actions
    $(".btn-move-up").on("click", function () {
        moveGame('move_up', $(this).data('game-id'));
    });

    $(".btn-move-down").on("click", function () {
        moveGame('move_down', $(this).data('game-id'));
    });

    $(".btn-move-top").on("click", function () {
        moveGame('move_top', $(this).data('game-id'));
    });

    $(".btn-move-bottom").on("click", function () {
        moveGame('move_bottom', $(this).data('game-id'));
    });

    function moveGame(action, gameId) {
        // Move game on the client-side (visual reordering)
        let gameCard = $(".row").find("[data-game-id='" + gameId + "']");
        switch (action) {
            case 'move_up':
                gameCard.insertBefore(gameCard.prev());
                break;
            case 'move_down':
                gameCard.insertAfter(gameCard.next());
                break;
            case 'move_top':
                gameCard.prependTo(gameCard.parent());
                break;
            case 'move_bottom':
                gameCard.appendTo(gameCard.parent());
                break;
        }
    }
}