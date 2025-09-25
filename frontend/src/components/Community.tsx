import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { ArrowLeft, Heart, MessageCircle, Share2, Plus, DollarSign, Lightbulb, ChefHat, Loader2 } from 'lucide-react';
import { User, CommunityPost, CommunityPostCreate } from '@/types';
import { communityApi } from '@/services/api';
import { shouldUseMockData } from '@/lib/demoMode';
import { storage } from '@/lib/storage';
import { mockCommunityPosts } from '@/lib/mockData';
import { showSuccess, showError } from '@/utils/toast';

interface CommunityProps {
  user: User;
  onBack: () => void;
}

export const Community = ({ user, onBack }: CommunityProps) => {
  const [posts, setPosts] = useState<CommunityPost[]>([]);
  const [activeTab, setActiveTab] = useState<'all' | 'recipes' | 'tips' | 'savings'>('all');
  const [showNewPost, setShowNewPost] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [newPost, setNewPost] = useState({
    title: '',
    content: '',
    post_type: 'tip' as 'recipe' | 'tip' | 'savings_story' | 'general'
  });

  useEffect(() => {
    loadPosts();
  }, []);

  const loadPosts = async () => {
    try {
      setLoading(true);
      
      if (shouldUseMockData()) {
        console.log('🧪 [Demo Mode] Using mock community posts');
        const savedPosts = storage.getCommunityPosts();
        if (savedPosts.length === 0) {
          storage.setCommunityPosts(mockCommunityPosts);
          setPosts(mockCommunityPosts);
        } else {
          setPosts(savedPosts);
        }
      } else {
        const response = await communityApi.getPosts({ page_size: 50 });
        setPosts(response.posts || []);
      }
    } catch (error) {
      console.warn('🧪 [Demo Mode] API failed, falling back to mock data:', error);
      const savedPosts = storage.getCommunityPosts();
      if (savedPosts.length === 0) {
        storage.setCommunityPosts(mockCommunityPosts);
        setPosts(mockCommunityPosts);
      } else {
        setPosts(savedPosts);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePost = async () => {
    if (!newPost.title.trim() || !newPost.content.trim()) return;

    try {
      setSubmitting(true);

      if (shouldUseMockData()) {
        console.log('🧪 [Demo Mode] Creating mock community post');
        const post: CommunityPost = {
          id: Date.now().toString(),
          user_id: user.id,
          title: newPost.title,
          content: newPost.content,
          post_type: newPost.post_type,
          tags: [],
          likes_count: 0,
          comments_count: 0,
          is_public: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          user_display_name: user.name
        };

        const updatedPosts = [post, ...posts];
        setPosts(updatedPosts);
        storage.setCommunityPosts(updatedPosts);
      } else {
        const postData: CommunityPostCreate = {
          title: newPost.title,
          content: newPost.content,
          post_type: newPost.post_type,
          is_public: true
        };

        const createdPost = await communityApi.createPost(postData);
        setPosts(prevPosts => [createdPost, ...prevPosts]);
      }
      
      setNewPost({ title: '', content: '', post_type: 'tip' });
      setShowNewPost(false);
      showSuccess('Your post has been shared with the community!');
    } catch (error) {
      console.error('Failed to create post:', error);
      showError('Failed to create post. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleLike = async (postId: string) => {
    try {
      if (shouldUseMockData()) {
        console.log('🧪 [Demo Mode] Liking mock post:', postId);
        const updatedPosts = posts.map(post => 
          post.id === postId 
            ? { ...post, likes_count: post.likes_count + 1, is_liked_by_user: true }
            : post
        );
        setPosts(updatedPosts);
        storage.setCommunityPosts(updatedPosts);
      } else {
        const updatedPost = await communityApi.likePost(postId);
        setPosts(prevPosts => 
          prevPosts.map(post => 
            post.id === postId ? updatedPost : post
          )
        );
      }
    } catch (error) {
      console.error('Failed to like post:', error);
      showError('Failed to like post. Please try again.');
    }
  };

  const filteredPosts = posts.filter(post => {
    if (activeTab === 'all') return true;
    if (activeTab === 'recipes') return post.post_type === 'recipe';
    if (activeTab === 'tips') return post.post_type === 'tip';
    if (activeTab === 'savings') return post.post_type === 'savings_story';
    return true;
  });

  const getPostIcon = (type: string) => {
    switch (type) {
      case 'recipe': return <ChefHat className="h-4 w-4" />;
      case 'tip': return <Lightbulb className="h-4 w-4" />;
      case 'savings_story': return <DollarSign className="h-4 w-4" />;
      default: return <MessageCircle className="h-4 w-4" />;
    }
  };

  const getPostTypeColor = (type: string) => {
    switch (type) {
      case 'recipe': return 'bg-blue-100 text-blue-600';
      case 'tip': return 'bg-yellow-100 text-yellow-600';
      case 'savings_story': return 'bg-green-100 text-green-600';
      default: return 'bg-gray-100 text-gray-600';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading community posts...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            <div className="flex items-center">
              <Button variant="ghost" onClick={onBack} className="mr-4">
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <div>
                <h1 className="text-xl font-semibold">Community</h1>
                <p className="text-sm text-gray-600">Share recipes, tips, and savings stories</p>
              </div>
            </div>
            <Button onClick={() => setShowNewPost(true)}>
              <Plus className="h-4 w-4 mr-2" />
              New Post
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tabs */}
        <div className="flex space-x-1 mb-6 bg-gray-100 p-1 rounded-lg">
          {[
            { key: 'all', label: 'All Posts' },
            { key: 'recipes', label: 'Recipes' },
            { key: 'tips', label: 'Tips' },
            { key: 'savings', label: 'Savings Stories' }
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* New Post Form */}
        {showNewPost && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Share with the Community</CardTitle>
              <CardDescription>
                Help other families with your recipes, tips, or savings stories
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Post Type</label>
                <div className="flex gap-2">
                  {[
                    { key: 'recipe', label: 'Recipe', icon: ChefHat },
                    { key: 'tip', label: 'Tip', icon: Lightbulb },
                    { key: 'savings_story', label: 'Savings Story', icon: DollarSign }
                  ].map(type => (
                    <Button
                      key={type.key}
                      variant={newPost.post_type === type.key ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setNewPost(prev => ({ ...prev, post_type: type.key as any }))}
                    >
                      <type.icon className="h-4 w-4 mr-1" />
                      {type.label}
                    </Button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Title</label>
                <Input
                  value={newPost.title}
                  onChange={(e) => setNewPost(prev => ({ ...prev, title: e.target.value }))}
                  placeholder="Give your post a catchy title..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Content</label>
                <Textarea
                  value={newPost.content}
                  onChange={(e) => setNewPost(prev => ({ ...prev, content: e.target.value }))}
                  placeholder="Share your story, recipe, or tip..."
                  rows={4}
                />
              </div>

              <div className="flex gap-2">
                <Button onClick={handleCreatePost} disabled={submitting}>
                  {submitting ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Sharing...
                    </>
                  ) : (
                    'Share Post'
                  )}
                </Button>
                <Button variant="outline" onClick={() => setShowNewPost(false)} disabled={submitting}>
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Posts */}
        <div className="space-y-6">
          {filteredPosts.map(post => (
            <Card key={post.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <div className={`p-1 rounded ${getPostTypeColor(post.post_type)}`}>
                        {getPostIcon(post.post_type)}
                      </div>
                      <Badge variant="outline" className="text-xs capitalize">
                        {post.post_type.replace('_', ' ')}
                      </Badge>
                      <span className="text-sm text-gray-500">
                        by {post.user_display_name || 'Anonymous'}
                      </span>
                      <span className="text-sm text-gray-400">
                        {new Date(post.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <CardTitle className="text-lg">{post.title}</CardTitle>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-gray-700 mb-4">{post.content}</p>
                
                <div className="flex items-center gap-4">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleLike(post.id)}
                    className="text-gray-600 hover:text-red-600"
                  >
                    <Heart className={`h-4 w-4 mr-1 ${post.is_liked_by_user ? 'fill-red-500 text-red-500' : ''}`} />
                    {post.likes_count}
                  </Button>
                  
                  <Button variant="ghost" size="sm" className="text-gray-600">
                    <MessageCircle className="h-4 w-4 mr-1" />
                    {post.comments_count}
                  </Button>
                  
                  <Button variant="ghost" size="sm" className="text-gray-600">
                    <Share2 className="h-4 w-4 mr-1" />
                    Share
                  </Button>
                </div>

                {/* Comments - Note: Comments will be loaded separately in a future enhancement */}
                {post.comments_count > 0 && (
                  <div className="mt-4 pt-4 border-t">
                    <p className="text-sm text-gray-500">
                      {post.comments_count} comment{post.comments_count !== 1 ? 's' : ''} - Click to view
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}

          {filteredPosts.length === 0 && (
            <div className="text-center py-12">
              <MessageCircle className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No posts yet</h3>
              <p className="text-gray-600 mb-4">
                Be the first to share a {activeTab === 'all' ? 'post' : activeTab.replace('s', '')} with the community!
              </p>
              <Button onClick={() => setShowNewPost(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Create First Post
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};