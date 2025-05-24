document.addEventListener('DOMContentLoaded', function () {
    // Spoiler reveal functionality
    const spoilerButtons = document.querySelectorAll('.reveal-spoiler-btn');
    spoilerButtons.forEach(button => {
        button.addEventListener('click', function () {
            const spoilerContent = this.previousElementSibling;
            if (spoilerContent && spoilerContent.classList.contains('spoiler-text')) {
                spoilerContent.classList.remove('hidden-spoiler');
                this.style.display = 'none'; // Hide the button after revealing
            }
        });
    });

    // Star rating interactivity (optional, for a nicer UI)
    const starRatingInputs = document.querySelectorAll('.star-rating input[type="radio"]');
    starRatingInputs.forEach(input => {
        input.addEventListener('change', function() {
            // You can add visual feedback here if needed, e.g., by changing star colors
            // console.log('Rated:', this.value);
        });
    });

    // Post voting AJAX
    document.querySelectorAll('.vote-btn[data-post-id]').forEach(button => {
        button.addEventListener('click', function() {
            const postId = this.dataset.postId;
            const voteType = this.dataset.voteType;
            
            // Using a relative path for the fetch URL.
            // This assumes that the base URL of the page is correct for this relative path.
            // E.g., if on /community/post/XYZ, then /community/post/XYZ/vote would be formed.
            // For more robustness, especially if your JS is global and URLs complex,
            // consider embedding the `url_for` generated URL in a data attribute.
            let voteUrl = `/community/post/${postId}/vote`; 

            const upvoteBtn = document.querySelector(`.upvote-btn[data-post-id='${postId}']`);
            const downvoteBtn = document.querySelector(`.downvote-btn[data-post-id='${postId}']`);
            const upvoteCountSpan = upvoteBtn ? upvoteBtn.querySelector('.upvote-count') : null;
            const downvoteCountSpan = downvoteBtn ? downvoteBtn.querySelector('.downvote-count') : null;

            fetch(voteUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    // 'X-CSRFToken': getCsrfToken() // Function to get CSRF token if using Flask-WTF/CSRFProtect
                },
                body: `vote_type=${voteType}`
            })
            .then(response => {
                if (!response.ok) {
                    // Attempt to parse error from JSON response, then fallback
                    return response.json()
                        .then(errData => { throw new Error(errData.message || `Server error (${response.status})`); })
                        .catch(() => { throw new Error(`Server error (${response.status})`); });
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    if (upvoteCountSpan) upvoteCountSpan.textContent = data.upvotes;
                    if (downvoteCountSpan) downvoteCountSpan.textContent = data.downvotes;
                    
                    if (upvoteBtn) upvoteBtn.classList.remove('active');
                    if (downvoteBtn) downvoteBtn.classList.remove('active');

                    if (data.new_vote_status === 'upvote' && upvoteBtn) {
                        upvoteBtn.classList.add('active');
                    } else if (data.new_vote_status === 'downvote' && downvoteBtn) {
                        downvoteBtn.classList.add('active');
                    }
                } else {
                    alert("Voting error: " + (data.message || "Unknown error"));
                }
            })
            .catch(error => {
                console.error('Fetch error for post voting:', error);
                alert('An error occurred while voting: ' + error.message);
            });
        });
    });

    // Basic reply form toggle for comments
    document.querySelectorAll('.reply-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const commentId = this.dataset.commentId; 
            const form = document.getElementById(`reply-form-${commentId}`);
            if (form) {
                const isHidden = form.style.display === 'none' || form.style.display === '';
                form.style.display = isHidden ? 'block' : 'none';
                if(isHidden) {
                    form.querySelector('textarea').focus(); // Auto-focus textarea when shown
                }
            }
        });
    });

    // Watchlist AJAX
    const watchlistForm = document.getElementById('watchlist-form');
    if (watchlistForm) {
        watchlistForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const animeId = this.dataset.animeId;
            const status = document.getElementById('watchlist-status-select').value;
            const url = `/anime/${animeId}/watchlist`; // Construct URL directly

            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    // 'X-CSRFToken': getCsrfToken(), // If using CSRF
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: `status=${status}`
            })
            .then(response => response.json())
            .then(data => {
                const messageDiv = document.getElementById('watchlist-message');
                const statusText = document.getElementById('current-watchlist-status-text');
                if (data.success) {
                    messageDiv.textContent = data.message;
                    messageDiv.className = 'flash success';
                    statusText.textContent = data.new_status ? data.new_status.replace('_', ' ').title() : 'Not on any list';
                    // Show/hide remove button
                    let removeBtn = document.getElementById('remove-watchlist-btn');
                    if (data.new_status && !removeBtn) {
                        // Add remove button if it doesn't exist
                        const newRemoveBtn = document.createElement('button');
                        newRemoveBtn.type = 'button';
                        newRemoveBtn.id = 'remove-watchlist-btn';
                        newRemoveBtn.className = 'button-sm button-danger';
                        newRemoveBtn.textContent = 'Remove from List';
                        watchlistForm.appendChild(newRemoveBtn);
                        addRemoveButtonListener(newRemoveBtn, animeId); // Attach listener
                    } else if (!data.new_status && removeBtn) {
                        removeBtn.remove();
                    }
                } else {
                    messageDiv.textContent = data.message || 'An error occurred.';
                    messageDiv.className = 'flash error';
                }
            })
            .catch(error => {
                console.error('Error updating watchlist:', error);
                const messageDiv = document.getElementById('watchlist-message');
                messageDiv.textContent = 'An error occurred: ' + error.message;
                messageDiv.className = 'flash error';
            });
        });
    }

    // Listener for dynamically added remove button
    function addRemoveButtonListener(button, animeId) {
        button.addEventListener('click', function() {
            handleRemoveFromWatchlist(animeId);
        });
    }
    
    // Initial listener for existing remove button
    const removeWatchlistBtn = document.getElementById('remove-watchlist-btn');
    if (removeWatchlistBtn) {
       addRemoveButtonListener(removeWatchlistBtn, watchlistForm.dataset.animeId);
    }

    function handleRemoveFromWatchlist(animeId) {
        const url = `/anime/${animeId}/watchlist`;
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                // 'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: 'status=remove'
        })
        .then(response => response.json())
        .then(data => {
            const messageDiv = document.getElementById('watchlist-message');
            const statusText = document.getElementById('current-watchlist-status-text');
             if (data.success) {
                messageDiv.textContent = data.message;
                messageDiv.className = 'flash success';
                statusText.textContent = 'Not on any list';
                document.getElementById('remove-watchlist-btn')?.remove(); // Remove the button itself
            } else {
                messageDiv.textContent = data.message || 'An error occurred.';
                messageDiv.className = 'flash error';
            }
        })
        .catch(error => {
            console.error('Error removing from watchlist:', error);
            const messageDiv = document.getElementById('watchlist-message');
            messageDiv.textContent = 'An error occurred: ' + error.message;
            messageDiv.className = 'flash error';
        });
    }
    
    // Tab functionality for user profile watchlists
    const tabButtons = document.querySelectorAll('.watchlist-tabs .tab-button');
    const tabContents = document.querySelectorAll('.watchlist-section .tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            this.classList.add('active');
            const targetTabContent = document.getElementById(this.dataset.tab);
            if(targetTabContent) { // check if element exists
                targetTabContent.classList.add('active');
            }
        });
    });

});

/*
// Example getCsrfToken function if you were using Flask-WTF and had a meta tag for CSRF token
function getCsrfToken() {
    const token = document.querySelector('meta[name="csrf-token"]');
    if (token) {
        return token.getAttribute('content');
    }
    // Or from a hidden input if your forms include it globally
    const hiddenInput = document.querySelector('input[name="csrf_token"]');
    if (hiddenInput) {
        return hiddenInput.value;
    }
    return null; 
}
*/
