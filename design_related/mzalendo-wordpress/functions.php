<?php
add_filter('next_posts_link_attributes', 'next_post_link_attributes');
add_filter('previous_posts_link_attributes', 'prev_post_link_attributes');

function next_post_link_attributes(){
	return 'class="next"';
}

function prev_post_link_attributes(){
	return 'class="prev"';
}
?>