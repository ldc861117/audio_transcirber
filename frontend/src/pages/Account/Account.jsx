import React, { useState, useEffect } from 'react';
import { useAuthStore } from '../../stores/authStore';
import { useSubscriptionStore } from '../../stores/subscriptionStore';
import { User, CreditCard, Clock, CheckCircle, AlertCircle, ExternalLink } from 'lucide-react';
import './Account.css';

const Account = () => {
  const { user } = useAuthStore();
  const { subscription, usage, invoices, fetchSubscription, fetchUsage, fetchInvoices, cancelSubscription, reactivateSubscription } = useSubscriptionStore();
  const [activeTab, setActiveTab] = useState('profile'); // 'profile' | 'subscription' | 'usage'

  useEffect(() => {
    fetchSubscription();
    fetchUsage();
    fetchInvoices();
  }, [fetchSubscription, fetchUsage, fetchInvoices]);

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <div className="account-container">
      <div className="account-header">
        <h1>账户管理</h1>
        <p>管理您的个人信息和订阅方案</p>
      </div>

      <div className="account-layout">
        <aside className="account-nav">
          <button 
            className={activeTab === 'profile' ? 'active' : ''} 
            onClick={() => setActiveTab('profile')}
          >
            <User size={18} /> 个人信息
          </button>
          <button 
            className={activeTab === 'subscription' ? 'active' : ''} 
            onClick={() => setActiveTab('subscription')}
          >
            <CreditCard size={18} /> 订阅管理
          </button>
          <button 
            className={activeTab === 'usage' ? 'active' : ''} 
            onClick={() => setActiveTab('usage')}
          >
            <Clock size={18} /> 用量历史
          </button>
        </aside>

        <main className="account-content">
          {activeTab === 'profile' && (
            <div className="account-card">
              <h2>个人信息</h2>
              <div className="profile-info">
                <div className="info-group">
                  <label>用户名</label>
                  <p>{user?.username}</p>
                </div>
                <div className="info-group">
                  <label>电子邮箱</label>
                  <p>{user?.email || '未设置'}</p>
                </div>
                <div className="info-group">
                  <label>角色</label>
                  <p style={{ textTransform: 'capitalize' }}>{user?.role || 'User'}</p>
                </div>
              </div>
              <button className="btn-secondary" style={{ marginTop: '1rem' }} onClick={() => alert('功能开发中')}>修改密码</button>
            </div>
          )}

          {activeTab === 'subscription' && (
            <div className="subscription-section">
              <div className="account-card">
                <h2>当前方案</h2>
                {subscription ? (
                  <div className="subscription-details">
                    <div className="plan-badge">
                      <span className="tier-name">{subscription.tier.toUpperCase()}</span>
                      <span className={`status-badge ${subscription.status}`}>
                        {subscription.status === 'active' ? '进行中' : '已取消'}
                      </span>
                    </div>
                    
                    <div className="details-grid">
                      <div className="detail-item">
                        <label>起始日期</label>
                        <p>{formatDate(subscription.current_period_start)}</p>
                      </div>
                      <div className="detail-item">
                        <label>到期日期</label>
                        <p>{formatDate(subscription.current_period_end)}</p>
                      </div>
                      <div className="detail-item">
                        <label>月度配额</label>
                        <p>{subscription.monthly_minutes_limit === -1 ? '无限' : `${subscription.monthly_minutes_limit} 分钟`}</p>
                      </div>
                      <div className="detail-item">
                        <label>账单周期</label>
                        <p style={{ textTransform: 'capitalize' }}>{subscription.billing_cycle || 'N/A'}</p>
                      </div>
                    </div>

                    <div className="action-buttons">
                      {subscription.tier !== 'free' && (
                        subscription.status === 'active' ? (
                          <button className="btn-danger" onClick={() => {
                            if(confirm('确定要取消订阅吗？到期前仍可使用。')) cancelSubscription();
                          }}>取消订阅</button>
                        ) : (
                          <button className="btn-primary" onClick={reactivateSubscription}>恢复订阅</button>
                        )
                      )}
                      <button className="btn-secondary" onClick={() => window.location.href='/pricing'}>升级方案</button>
                    </div>
                  </div>
                ) : (
                  <p>加载订阅信息中...</p>
                )}
              </div>

              <div className="account-card">
                <h2>最近账单</h2>
                {invoices.length > 0 ? (
                  <table className="invoices-table">
                    <thead>
                      <tr>
                        <th>日期</th>
                        <th>金额</th>
                        <th>状态</th>
                        <th>操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      {invoices.map(invoice => (
                        <tr key={invoice.id}>
                          <td>{formatDate(invoice.created_at)}</td>
                          <td>{(invoice.amount / 100).toFixed(2)} {invoice.currency.toUpperCase()}</td>
                          <td>
                            <span className={`status-text ${invoice.status}`}>
                              {invoice.status === 'paid' ? '已支付' : '待支付'}
                            </span>
                          </td>
                          <td>
                            {invoice.stripe_invoice_id && (
                              <button className="btn-icon" title="查看 Stripe 账单" onClick={() => alert('Stripe 账单页面')}>
                                <ExternalLink size={16} />
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="empty-msg">暂无账单记录</p>
                )}
              </div>
            </div>
          )}

          {activeTab === 'usage' && (
            <div className="account-card">
              <h2>用量详情</h2>
              {usage ? (
                <div className="usage-stats">
                  <div className="stat-card">
                    <label>本月已消耗</label>
                    <div className="stat-value">{Math.round(usage.minutes_used)} <span>分钟</span></div>
                  </div>
                  <div className="stat-card">
                    <label>剩余配额</label>
                    <div className="stat-value">
                      {usage.monthly_minutes_limit === -1 ? '∞' : Math.max(0, usage.monthly_minutes_limit - Math.round(usage.minutes_used))} 
                      <span>分钟</span>
                    </div>
                  </div>
                </div>
              ) : (
                <p>正在加载用量数据...</p>
              )}
              
              <div className="usage-warning">
                <AlertCircle size={18} />
                <p>配额每月 1 号重置。未使用的分钟数不会结转到下个月。</p>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default Account;
