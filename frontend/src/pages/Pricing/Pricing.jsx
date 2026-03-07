import React, { useEffect, useState } from 'react';
import { useSubscriptionStore } from '../../stores/subscriptionStore';
import { Check, X } from 'lucide-react';
import './Pricing.css';

const Pricing = () => {
  const { plans, subscription, fetchPlans, fetchSubscription, checkout } = useSubscriptionStore();
  const [billingCycle, setBillingCycle] = useState('monthly'); // 'monthly' | 'yearly'

  useEffect(() => {
    fetchPlans();
    fetchSubscription();
  }, [fetchPlans, fetchSubscription]);

  const handleUpgrade = (tier) => {
    checkout(tier, billingCycle);
  };

  if (!plans || plans.length === 0) {
    return <div style={{ textAlign: 'center', padding: '4rem' }}>正在加载方案...</div>;
  }

  return (
    <div className="pricing-container">
      <div className="pricing-header">
        <h1>选择适合您的方案</h1>
        <p>释放 AI 转录的全部潜力</p>
        
        <div className="billing-toggle">
          <button 
            className={billingCycle === 'monthly' ? 'active' : ''} 
            onClick={() => setBillingCycle('monthly')}
          >
            月付
          </button>
          <button 
            className={billingCycle === 'yearly' ? 'active' : ''} 
            onClick={() => setBillingCycle('yearly')}
          >
            年付 <span className="save-badge">节省 20%</span>
          </button>
        </div>
      </div>

      <div className="pricing-grid">
        {plans.map((plan) => {
          const isCurrent = subscription?.tier === plan.id;
          const price = billingCycle === 'monthly' ? plan.price_monthly_cents : plan.price_yearly_cents;
          
          return (
            <div key={plan.id} className={`pricing-card ${plan.id === 'pro' ? 'featured' : ''}`}>
              {plan.id === 'pro' && <div className="featured-badge">最受欢迎</div>}
              <div className="card-header">
                <h2>{plan.display_name}</h2>
                <div className="price">
                  <span className="currency">¥</span>
                  <span className="amount">{price / 100}</span>
                  <span className="period">/{billingCycle === 'monthly' ? '月' : '年'}</span>
                </div>
              </div>
              
              <div className="card-features">
                <ul>
                  <li>
                    <Check size={18} className="icon-check" />
                    <span>每月 {plan.monthly_minutes === -1 ? '无限' : plan.monthly_minutes} 分钟</span>
                  </li>
                  <li>
                    <Check size={18} className="icon-check" />
                    <span>单文件最大 {plan.max_single_minutes === -1 ? '不限' : plan.max_single_minutes} 分钟</span>
                  </li>
                  <li>
                    {plan.features.diarization ? <Check size={18} className="icon-check" /> : <X size={18} className="icon-x" />}
                    <span>说话人识别</span>
                  </li>
                  <li>
                    <Check size={18} className="icon-check" />
                    <span>支持格式: {plan.features.export_formats.join(', ')}</span>
                  </li>
                  <li>
                    {plan.features.api_access ? <Check size={18} className="icon-check" /> : <X size={18} className="icon-x" />}
                    <span>API 访问</span>
                  </li>
                </ul>
              </div>

              <div className="card-footer">
                {isCurrent ? (
                  <button className="btn-current" disabled>当前方案</button>
                ) : (
                  <button 
                    className={plan.id === 'pro' ? 'btn-primary' : 'btn-secondary'}
                    onClick={() => handleUpgrade(plan.id)}
                  >
                    {plan.price_monthly_cents === 0 ? '开始使用' : '立即升级'}
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default Pricing;
