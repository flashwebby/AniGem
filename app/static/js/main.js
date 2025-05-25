document.addEventListener('DOMContentLoaded', function () {
    // --- Helper Functions ---
    /**
     * Shows a dynamic Bootstrap alert message.
     * @param {string} message - The message to display.
     * @param {string} category - 'success', 'error' (or 'danger'), 'warning', 'info'.
     * @param {string} containerId - The ID of the container where the flash message should be appended. Defaults to 'flash-message-container'.
     * @param {number} timeout - Duration in ms before the message fades out. 0 for no timeout.
     */
    function showFlashMessage(message, category, containerId = 'flash-message-container', timeout = 5000) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.warn(`Flash message container with ID '${containerId}' not found.`);
            alert(`${category.toUpperCase()}: ${message}`); // Fallback to alert
            return;
        }

        const alertType = category === 'error' ? 'danger' : category; // Bootstrap uses 'danger' for error
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${alertType} alert-dismissible fade show`;
        alertDiv.role = 'alert';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        `;
        // Prepend to show at the top
        container.prepend(alertDiv);

        if (timeout > 0) {
            setTimeout(() => {
                // Bootstrap's close method to trigger fade out
                if (typeof(bootstrap) !== 'undefined' && bootstrap.Alert) { // Bootstrap 5
                    const bsAlert = bootstrap.Alert.getInstance(alertDiv) || new bootstrap.Alert(alertDiv);
                    bsAlert.close();
                } else if (typeof($) !== 'undefined' && $.fn.alert) { // Bootstrap 4 (jQuery)
                    $(alertDiv).alert('close');
                } else { // Fallback if Bootstrap JS isn't available for closing
                    alertDiv.remove();
                }
            }, timeout);
        }
    }

    /**
     * Generic Fetch API wrapper for JSON requests.
     * @param {string} url - The endpoint URL.
     * @param {string} method - HTTP method (GET, POST, PUT, DELETE).
     * @param {object} body - The request body for POST/PUT.
     * @returns {Promise<object>} - The JSON response.
     */
    async function fetchJSON(url, method = 'GET', body = null) {
        const headers = {
            'X-Requested-With': 'XMLHttpRequest', // Standard header for AJAX
        };
        if (method === 'POST' || method === 'PUT') {
            headers['Content-Type'] = 'application/x-www-form-urlencoded'; // or 'application/json' if backend expects JSON
        }
        // Add CSRF token if available (conceptual, see getCsrfToken() example below)
        // const csrfToken = getCsrfToken();
        // if (csrfToken) headers['X-CSRFToken'] = csrfToken;

        const options = { method, headers };
        if (body) {
            // If sending URL-encoded form data
            options.body = new URLSearchParams(body).toString();
            // If sending JSON:
            // options.body = JSON.stringify(body);
            // headers['Content-Type'] = 'application/json';
        }

        const response = await fetch(url, options);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ message: `HTTP error ${response.status}` }));
            throw new Error(errorData.message || `HTTP error ${response.status}`);
        }
        return response.json();
    }


    // --- Enhanced Spoiler Reveal Functionality ---
    document.querySelectorAll('.reveal-spoiler-btn').forEach(button => {
        button.addEventListener('click', function() {
            const spoilerContent = this.previousElementSibling;
            if (spoilerContent && spoilerContent.classList.contains('spoiler-text')) {
                if (spoilerContent.classList.contains('hidden-spoiler')) {
                    spoilerContent.classList.remove('hidden-spoiler');
                    spoilerContent.classList.add('revealed');
                    this.textContent = 'Hide Spoiler';
                } else {
                    spoilerContent.classList.add('hidden-spoiler');
                    spoilerContent.classList.remove('revealed');
                    this.textContent = 'Reveal Spoiler';
                }
            }
        });
    });

    // --- AJAX for Rating Submission ---
    const ratingForm = document.getElementById('rating-form');
    if (ratingForm) {
        // Event delegation for star clicks if we want instant submission on click
        const starRatingContainer = ratingForm.querySelector('.star-rating');
        if (starRatingContainer) {
            starRatingContainer.addEventListener('click', function(event) {
                if (event.target.type === 'radio' && event.target.name === 'score') {
                    // Optionally submit form here or just update UI and wait for explicit submit
                    // For now, we'll rely on the explicit submit button
                    // ratingForm.requestSubmit(); // Or handle AJAX directly
                }
            });
        }

        ratingForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            const formData = new FormData(this);
            const score = formData.get('score');
            if (!score) {
                showFlashMessage('Please select a rating.', 'warning');
                return;
            }

            try {
                const data = await fetchJSON(this.action, 'POST', { score });
                if (data.success) {
                    showFlashMessage(data.message || 'Rating submitted successfully!', 'success');
                    if (document.getElementById('average-rating')) {
                        document.getElementById('average-rating').textContent = `${data.new_average_rating.toFixed(1)} / 10`;
                    }
                    if (document.getElementById('user-current-rating')) {
                        document.getElementById('user-current-rating').innerHTML = `<p>Your current rating: ${score}/10</p>`;
                    }
                } else {
                    showFlashMessage(data.message || 'Failed to submit rating.', 'error');
                }
            } catch (error) {
                showFlashMessage(`Error: ${error.message}`, 'error');
                console.error('Rating submission error:', error);
            }
        });
    }

    // --- AJAX for Review Submission ---
    const reviewForm = document.getElementById('review-form');
    if (reviewForm) {
        reviewForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            const formData = new FormData(this);
            const reviewData = {
                text_content: formData.get('text_content'),
                is_spoiler: formData.get('is_spoiler') === 'on' // Checkbox value
            };

            try {
                const data = await fetchJSON(this.action, 'POST', reviewData);
                if (data.success) {
                    showFlashMessage(data.message || 'Review submitted successfully!', 'success');
                    this.reset(); // Clear the form

                    // Dynamically add the new review to the list
                    const reviewListContainer = document.getElementById('review-list-container');
                    if (reviewListContainer && data.review_html) { // Assuming backend sends rendered HTML for the new review
                        const noReviewsMessage = document.getElementById('no-reviews-message');
                        if(noReviewsMessage) noReviewsMessage.remove();
                        
                        reviewListContainer.insertAdjacentHTML('afterbegin', data.review_html);
                        // Re-attach event listeners if new review has interactive elements (like vote buttons)
                        // This is a simplified approach; a more robust solution might involve re-rendering the list or targeted event delegation.
                        attachVoteEventListeners(reviewListContainer.firstElementChild); 
                        // Re-attach spoiler button listener if the new review has one
                        const newSpoilerBtn = reviewListContainer.firstElementChild.querySelector('.reveal-spoiler-btn');
                        if (newSpoilerBtn) {
                             newSpoilerBtn.addEventListener('click', function() { /* ... spoiler logic ... */ });
                        }
                    }
                } else {
                    showFlashMessage(data.message || 'Failed to submit review.', 'error');
                }
            } catch (error) {
                showFlashMessage(`Error: ${error.message}`, 'error');
                console.error('Review submission error:', error);
            }
        });
    }
    
    // --- AJAX for Comment Submission (Post Detail Page) ---
    const commentForm = document.querySelector('form[action*="/community/post/"][action*="/comment"]'); // More generic selector
    if (commentForm) {
        commentForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            const formData = new FormData(this);
            const commentData = {
                text_content: formData.get('text_content'),
                parent_comment_id: formData.get('parent_comment_id') || null
            };

            try {
                const data = await fetchJSON(this.action, 'POST', commentData);
                if (data.success) {
                    showFlashMessage(data.message || 'Comment posted successfully!', 'success');
                    this.reset();
                    if (data.comment_html) {
                        // Determine where to append the comment
                        const parentCommentId = commentData.parent_comment_id;
                        let commentContainer;
                        if (parentCommentId) {
                            const parentCommentElement = document.getElementById(`comment-${parentCommentId}`);
                            commentContainer = parentCommentElement ? parentCommentElement.querySelector('.replies') : null;
                            // If .replies container doesn't exist, create it
                            if (parentCommentElement && !commentContainer) {
                                commentContainer = document.createElement('div');
                                commentContainer.className = 'replies mt-3'; // Bootstrap media object replies container
                                parentCommentElement.querySelector('.media-body').appendChild(commentContainer);
                            }
                        } else {
                             // Top-level comment, find the main comment thread
                            commentContainer = document.querySelector('.comment-thread.list-group'); // From _comment.html
                            // Remove "no comments yet" message if it exists
                             const noCommentsMessage = commentContainer ? commentContainer.querySelector('.alert-info, p.text-muted') : null;
                             if(noCommentsMessage && noCommentsMessage.textContent.includes("No comments yet")) noCommentsMessage.remove();
                        }
                        
                        if (commentContainer) {
                            commentContainer.insertAdjacentHTML('beforeend', data.comment_html);
                            // Re-attach listeners for new comment's reply button, etc.
                            const newCommentElement = commentContainer.lastElementChild;
                            attachReplyEventListeners(newCommentElement);
                        } else {
                            // Fallback: reload or show message to refresh. This shouldn't happen if structure is correct.
                            console.warn("Could not find appropriate container to append comment.");
                            window.location.reload(); // Simplest fallback
                        }
                    }
                } else {
                    showFlashMessage(data.message || 'Failed to post comment.', 'error');
                }
            } catch (error) {
                showFlashMessage(`Error: ${error.message}`, 'error');
                console.error('Comment submission error:', error);
            }
        });
    }


    // --- AJAX for Upvote/Downvote (Generic for Reviews and Posts/Comments) ---
    function attachVoteEventListeners(parentElement = document) {
        parentElement.querySelectorAll('.vote-form').forEach(form => {
            // Prevent multiple listeners if re-attaching
            if (form.dataset.ajaxAttached) return;
            form.dataset.ajaxAttached = true;

            form.addEventListener('submit', async function(event) {
                event.preventDefault();
                const reviewId = this.dataset.reviewId; // For reviews
                const postId = this.dataset.postId; // For posts
                const commentId = this.dataset.commentId; // For post comments
                const voteType = this.dataset.voteType;
                
                let url = this.action; // Get URL from form action attribute
                if (!url) { // Fallback if action is not set (though it should be)
                    if (reviewId) url = `/ratings_reviews/review/${reviewId}/vote`;
                    else if (postId) url = `/community/post/${postId}/vote`; 
                    // else if (commentId) url = `/community/comment/${commentId}/vote`; // Backend route needed
                    else {
                        console.error("No ID found for voting target.");
                        return;
                    }
                }

                try {
                    const data = await fetchJSON(url, 'POST', { vote_type: voteType });
                    if (data.success) {
                        // Update counts
                        const upvoteBtn = this.closest('.review-actions, .post-actions').querySelector('.upvote-btn, .upvote-btn');
                        const downvoteBtn = this.closest('.review-actions, .post-actions').querySelector('.downvote-btn, .downvote-btn');
                        
                        if (upvoteBtn) {
                            const upvoteCountSpan = upvoteBtn.querySelector('.upvote-count');
                            if(upvoteCountSpan) upvoteCountSpan.textContent = data.upvotes;
                            upvoteBtn.classList.remove('active');
                            if (data.new_vote_status === 'upvote') upvoteBtn.classList.add('active');
                        }
                        if (downvoteBtn) {
                             const downvoteCountSpan = downvoteBtn.querySelector('.downvote-count');
                            if(downvoteCountSpan) downvoteCountSpan.textContent = data.downvotes;
                            downvoteBtn.classList.remove('active');
                            if (data.new_vote_status === 'downvote') downvoteBtn.classList.add('active');
                        }
                        if (data.message) {
                           // showFlashMessage(data.message, 'success', 'flash-message-container', 2000); // Short lived success
                        }
                    } else {
                        showFlashMessage(data.message || 'Voting failed.', 'error');
                    }
                } catch (error) {
                    showFlashMessage(`Error: ${error.message}`, 'error');
                    console.error('Voting error:', error);
                }
            });
        });
    }
    attachVoteEventListeners(); // Initial attachment for existing elements


    // --- Basic Reply Form Toggle for Comments (from previous iteration, ensure it's robust) ---
    function attachReplyEventListeners(parentElement = document) {
        parentElement.querySelectorAll('.reply-link').forEach(link => {
            // Prevent multiple listeners
            if (link.dataset.replyAttached) return;
            link.dataset.replyAttached = true;

            link.addEventListener('click', function(e) {
                e.preventDefault();
                const targetFormId = this.dataset.formTarget; // e.g., reply-form-COMMENT_ID
                const form = document.getElementById(targetFormId);
                if (form) {
                    const isHidden = form.style.display === 'none' || form.style.display === '';
                    form.style.display = isHidden ? 'block' : 'none';
                    if (isHidden) {
                        form.querySelector('textarea').focus();
                    }
                }
            });
        });
    }
    attachReplyEventListeners(); // Initial attachment


    // --- Watchlist AJAX (from previous iteration, kept for completeness) ---
    // ... (existing watchlist AJAX code, ensure it uses showFlashMessage and fetchJSON if refactoring)
    // For brevity, I'm omitting the full watchlist code here but it should be retained and potentially refactored.
    // Key parts to check/update:
    // - Use fetchJSON for the AJAX call.
    // - Use showFlashMessage for feedback.
    // - Ensure dynamic button updates are correct.

    // Example of refactoring a part of watchlist AJAX:
    const watchlistForm = document.getElementById('watchlist-form'); // This ID needs to be on the watchlist form in anime_detail.html
    if (watchlistForm) {
        watchlistForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const animeId = this.dataset.animeId; // Ensure data-anime-id is on the form
            const statusSelect = document.getElementById('watchlist-status-select'); // Ensure this select exists
            const status = statusSelect ? statusSelect.value : null;

            if (!status) {
                showFlashMessage('Please select a status.', 'warning');
                return;
            }
            // The URL should ideally come from a data attribute or be constructed safely
            const url = this.action || `/anime/${animeId}/watchlist`; 

            try {
                const data = await fetchJSON(url, 'POST', { status });
                const statusTextElement = document.getElementById('current-watchlist-status-text'); // Element to show current status

                if (data.success) {
                    showFlashMessage(data.message || 'Watchlist updated!', 'success');
                    if (statusTextElement) {
                        statusTextElement.textContent = data.new_status ? data.new_status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Not on list';
                    }
                    // Potentially update other UI elements like a remove button
                } else {
                    showFlashMessage(data.message || 'Failed to update watchlist.', 'error');
                }
            } catch (error) {
                showFlashMessage(`Error: ${error.message}`, 'error');
                console.error('Watchlist update error:', error);
            }
        });
    }
    // ... (rest of watchlist AJAX, including remove button logic)

});

/*
// Example getCsrfToken function (conceptual, if needed)
function getCsrfToken() {
    const tokenElement = document.querySelector('meta[name="csrf-token"]');
    if (tokenElement) {
        return tokenElement.getAttribute('content');
    }
    const tokenInput = document.querySelector('input[name="csrf_token"]');
    if (tokenInput) {
        return tokenInput.value;
    }
    return null; 
}
*/
