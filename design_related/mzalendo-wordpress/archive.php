<?php get_header();?>
	<div id="blog-title-space">
		<?php /* If this is a category archive */ if (is_category()) { ?>
		<h1>Currently browsing '<?php echo single_cat_title(); ?>'</h1>
		<?php /* If this is a tag archive */ } elseif (is_tag()) { ?>
		<h1>Currently browsing '<?php echo single_tag_title() ?>'</h1>
		<?php /* If this is a date archive */ } elseif (is_date()) { ?>
		<h1>Entries from <?php the_time('F jS, Y'); ?></h1>
		<?php /* If this is a monthly archive */ } elseif (is_month()) { ?>
		<h1>Entries from <?php the_time('F Y'); ?></h1>
		<?php /* If this is a yearly archive */ } elseif (is_year()) { ?>
		<h1>Entries from <?php the_time('Y'); ?></h1>
		<?php /* If this is an author archive */ } elseif (is_author()) {
			$curauth = (isset($_GET['author_name'])) ? get_user_by('slug', $author_name) : get_userdata(intval($author));
		?>
		<h1>Currently browsing posts by <?php echo $curauth->display_name; ?></h1>
		<?php /* If this is a search */ } elseif (is_search()) { ?>
		<h1>Search Results</h1>
		<?php } ?>
	</div>

	<div id="blog-posts">
		<?php if ( have_posts() ) : while ( have_posts() ) : the_post(); ?>
			<div id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
				<h2><a href="<?php the_permalink() ?>" rel="bookmark" title="Permanent Link to <?php the_title(); ?>"><?php the_title(); ?></a></h2>
				<p class="meta">Posted by <?php echo the_author_posts_link();?> on <?php echo the_time('jS F Y');?></p>
				<p class="comments-link"><?php comments_popup_link('No Comments', '1 Comment', '% Comments');?></p>
				<section>
					<p class="categories">Categories: <?php echo the_category(' ');?></p>

					<div class="post-entry">
						<?php the_content('Read more &raquo;'); ?>
					</div>
				</section>
			</div>
		<?php endwhile; else: ?>
			<h2>Not Found</h2>
			<p>Sorry, but you are looking for something that isn't here.</p>
			<?php get_search_form(); ?>
		<?php endif; ?>

		<?php if (  $wp_query->max_num_pages > 1 ) : ?>
			<div class="pagination">
				<?php previous_posts_link( __( 'Previous' ) ); ?>
				<?php next_posts_link( __( 'Next' ) ); ?>
			</div>
		<?php endif; ?>
	</div>

	<?php get_sidebar(); ?>

<?php get_footer(); ?>