"""
API routes for AJAX functionality
"""
from flask import Blueprint, jsonify, request
from app.models.contract import Contract
from app.models.client import Client
from app.models.user import User
from app import db
from sqlalchemy import or_

api = Blueprint('api', __name__, url_prefix='/api')


@api.route('/search/suggestions')
def search_suggestions():
    """Get search suggestions based on query"""
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify({'suggestions': []})
    
    suggestions = []
    
    try:
        # Search contracts
        contract_suggestions = Contract.query.filter(
            or_(
                Contract.title.ilike(f'%{query}%'),
                Contract.description.ilike(f'%{query}%'),
                Contract.contract_type.ilike(f'%{query}%')
            )
        ).limit(5).all()
        
        for contract in contract_suggestions:
            suggestions.append({
                'type': 'contract',
                'text': contract.title,
                'category': 'Contract',
                'id': contract.id,
                'url': f'/contracts/{contract.id}'
            })
        
        # Search clients
        client_suggestions = Client.query.filter(
            or_(
                Client.name.ilike(f'%{query}%'),
                Client.organization.ilike(f'%{query}%'),
                Client.email.ilike(f'%{query}%')
            )
        ).limit(5).all()
        
        for client in client_suggestions:
            suggestions.append({
                'type': 'client',
                'text': client.name,
                'category': 'Client',
                'id': client.id,
                'url': f'/clients/{client.id}'
            })
        
        # Search users (if admin)
        # user_suggestions = User.query.filter(
        #     or_(
        #         User.username.ilike(f'%{query}%'),
        #         User.email.ilike(f'%{query}%')
        #     )
        # ).limit(3).all()
        
        # for user in user_suggestions:
        #     suggestions.append({
        #         'type': 'user',
        #         'text': user.username,
        #         'category': 'User',
        #         'id': user.id,
        #         'url': f'/users/{user.id}'
        #     })
        
        # Add common search terms
        common_terms = [
            'active', 'expired', 'draft', 'review', 'service', 'employment',
            'lease', 'purchase', 'nda', 'partnership', 'contract', 'agreement'
        ]
        
        for term in common_terms:
            if query.lower() in term.lower() and term not in [s['text'] for s in suggestions]:
                suggestions.append({
                    'type': 'term',
                    'text': term,
                    'category': 'Common Term',
                    'id': None,
                    'url': None
                })
        
        # Limit total suggestions
        suggestions = suggestions[:10]
        
        return jsonify({
            'suggestions': suggestions,
            'query': query,
            'count': len(suggestions)
        })
        
    except Exception as e:
        print(f"Error in search suggestions: {e}")
        return jsonify({
            'suggestions': [],
            'error': 'Failed to fetch suggestions'
        }), 500


@api.route('/search/quick')
def quick_search():
    """Quick search across all entities"""
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify({'results': []})
    
    results = []
    
    try:
        # Quick contract search
        contracts = Contract.query.filter(
            or_(
                Contract.title.ilike(f'%{query}%'),
                Contract.description.ilike(f'%{query}%')
            )
        ).limit(3).all()
        
        for contract in contracts:
            results.append({
                'type': 'contract',
                'title': contract.title,
                'description': contract.description[:100] + '...' if len(contract.description) > 100 else contract.description,
                'status': contract.status,
                'url': f'/contracts/{contract.id}',
                'icon': 'bi-file-earmark-text'
            })
        
        # Quick client search
        clients = Client.query.filter(
            or_(
                Client.name.ilike(f'%{query}%'),
                Client.organization.ilike(f'%{query}%')
            )
        ).limit(3).all()
        
        for client in clients:
            results.append({
                'type': 'client',
                'title': client.name,
                'description': client.organization or 'No organization',
                'status': 'Active' if client.id else 'Inactive',
                'url': f'/clients/{client.id}',
                'icon': 'bi-people'
            })
        
        return jsonify({
            'results': results,
            'query': query,
            'count': len(results)
        })
        
    except Exception as e:
        print(f"Error in quick search: {e}")
        return jsonify({
            'results': [],
            'error': 'Failed to perform quick search'
        }), 500


@api.route('/search/stats')
def search_stats():
    """Get search statistics"""
    try:
        total_contracts = Contract.query.count()
        active_contracts = Contract.query.filter_by(status='active').count()
        expiring_soon = Contract.query.filter(
            Contract.expiration_date.isnot(None)
        ).count()
        
        total_clients = Client.query.count()
        
        return jsonify({
            'contracts': {
                'total': total_contracts,
                'active': active_contracts,
                'expiring_soon': expiring_soon
            },
            'clients': {
                'total': total_clients
            }
        })
        
    except Exception as e:
        print(f"Error in search stats: {e}")
        return jsonify({'error': 'Failed to fetch search statistics'}), 500
