<?php // Do not delete these lines
if (!empty($_SERVER['SCRIPT_FILENAME']) && 'comments.php' == basename($_SERVER['SCRIPT_FILENAME']))
	die ('Please do not load this page directly. Thanks!');
if ( post_password_required() ) { ?>
	<p><?php _e("This post is password protected. Enter the password to view comments."); ?></p>
<?php
	return;
} /* You can start editing below. */ ?>


<div id="comments">
	<?php if ( have_comments() ) { ?>
		<h2 class="comments-heading"><?php comments_popup_link('No Comments', '1 Comment', '% Comments'); ?></h2>
		<!-- <p>Please use this facility responsibly. It is NOT a discussion forum. Try to keep your comments relevant to constituency related issues. We WILL delete comments we deem inappropriate or irrelevant to the purposes of this initiative. As we don't have the capacity to do otherwise, we will only accept comments in English or Kiswahil.</p> -->

		<ul class="comments comment-list">
		<?php 
			// wp_list_comments();
			$theid = get_the_ID();
			$thepermalink = get_permalink();
			$args = array(
				'post_id' => $theid,
				'order' => 'ASC'
			);
			$comments = get_comments($args);
			foreach($comments as $comment) :
		?>
			<li id="comment-<?php echo $comment->comment_ID ?>">
				<?php echo get_avatar( $comment->comment_author_email, '60'); ?> 
				<section>
					<p class="meta">by <a href="<?php if($comment->comment_author_url != ''){echo $comment->comment_author_url;}else{echo 'mailto:'.$comment->comment_author_email;} ?>"><?php echo $comment->comment_author ?></a> on <?php echo comment_date( 'jS F Y', $comment->comment_ID ); ?></p>

					<ul class="tools">
	                    <li><a href="<?php echo $thepermalink.'#comment-'.$comment->comment_ID ?>">link</a></li>
                	</ul>

                	<p><?php echo $comment->comment_content ?></p>
				</section>
			</li>
		<?php
			endforeach;
		?>
		</ul>
	<?php } else { // this is displayed if there are no comments so far ?>
		<?php if ('open' == $post-> comment_status) { ?> 
			<!-- If comments are open, but there are no comments. -->
			<h2 class="comments-heading"><?php comments_popup_link('No Comments', '1 Comment', '% Comments'); ?></h2>
		<?php } else { // comments are closed ?>
			<!-- If comments are closed. -->
		<?php } ?>
	<?php } ?>
</div>

<?php if ('open' == $post-> comment_status) : ?>
	<div id="respond">
		<h2 class="respond-heading"><?php comment_form_title('Post a Comment', 'Leave a Reply to %s'); ?></h2>
		<?php if ( get_option('comment_registration') && !$user_ID ) : ?>	
			<p>You must <a href="<?php echo get_option('siteurl'); ?>/wp-login.php?redirect_to=<?php the_permalink(); ?>">log in</a> to post a comment.</p>	
		<?php else : ?>
			<form action="<?php echo get_option('siteurl'); ?>/wp-comments-post.php" method="post" id="comment-form">

			<?php if ( $user_ID ) { ?>
				<p>Logged in as <a href="<?php echo get_option('siteurl'); ?>/wp-admin/profile.php"><?php echo $user_identity; ?></a>. <a href="<?php echo wp_logout_url(get_permalink()); ?>" title="<?php _e('Log out of this account') ?>">Logout &raquo;</a></p>
			<?php } ?>
			<?php if ( !$user_ID ) { ?>
				<div class="comment-field">
					<label for="author">Name</label>
					<input placeholder="Name" type="text" name="author" id="author" value="<?php echo $comment_author; ?>" tabindex="1" />
				</div>
				<div class="comment-field">
					<label for="email">Email</label>
					<input placeholder="Email" type="text" name="email" id="email" value="<?php echo $comment_author_email; ?>" tabindex="2" />
				</div>
				<div class="comment-field">
					<label for="url">Website</label>
					<input placeholder="Website" type="text" name="url" id="url" value="<?php echo $comment_author_url; ?>" tabindex="3" />
				</div>
			<?php } ?>
				<div class="comment-field">
					<label for="comment">Comment</label>
					<textarea placeholder="Comment" name="comment" id="comment" tabindex="4"></textarea>
				</div>			
				
				<?php comment_id_fields(); ?>
				<button class="btn-text-green" name="submit" type="submit" id="submit" tabindex="5">Submit</button>

				<?php do_action('comment_form', $post->ID); ?>	
			</form>
		<?php endif; // If registration required and not logged in ?>		
	</div><?php //#respond ?>
	
	<div class="pagination">
		<?php previous_comments_link() ?>&nbsp;
		<?php next_comments_link() ?>&nbsp;
	</div>
<?php endif; // if you delete this the sky will fall on your head ?>