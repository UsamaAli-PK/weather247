import React, { useState, useEffect } from 'react';
import { Search, Plus, MapPin, Loader2 } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent } from './ui/card';
import apiService from '../services/api';

const CitySearch = ({ onCityAdded, onCitySelected }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);

  useEffect(() => {
    const searchCities = async () => {
      if (query.length < 2) {
        setResults([]);
        setShowResults(false);
        return;
      }

      setLoading(true);
      try {
        const response = await apiService.searchCities(query);
        setResults(response.results || []);
        setShowResults(true);
      } catch (error) {
        console.error('City search error:', error);
        setResults([]);
      } finally {
        setLoading(false);
      }
    };

    const debounceTimer = setTimeout(searchCities, 300);
    return () => clearTimeout(debounceTimer);
  }, [query]);

  const handleAddCity = async (city) => {
    try {
      setLoading(true);
      const response = await apiService.addCity({
        name: city.name,
        country: city.country,
        latitude: city.latitude,
        longitude: city.longitude
      });
      
      if (onCityAdded) {
        onCityAdded(response.city);
      }
      
      setQuery('');
      setShowResults(false);
    } catch (error) {
      console.error('Add city error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectCity = (city) => {
    if (onCitySelected) {
      onCitySelected(city);
    }
    setQuery('');
    setShowResults(false);
  };

  return (
    <div className="relative">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
        <Input
          type="text"
          placeholder="Search for cities..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="pl-10 pr-4"
          onFocus={() => query.length >= 2 && setShowResults(true)}
        />
        {loading && (
          <Loader2 className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 animate-spin text-gray-400" />
        )}
      </div>

      {showResults && (
        <Card className="absolute top-full left-0 right-0 mt-1 z-50 max-h-80 overflow-y-auto">
          <CardContent className="p-0">
            {results.length > 0 ? (
              <div className="divide-y">
                {results.map((city, index) => (
                  <div
                    key={`${city.name}-${city.country}-${index}`}
                    className="p-3 hover:bg-gray-50 cursor-pointer flex items-center justify-between"
                  >
                    <div 
                      className="flex items-center space-x-3 flex-1"
                      onClick={() => city.exists ? handleSelectCity(city) : null}
                    >
                      <MapPin className="h-4 w-4 text-gray-400" />
                      <div>
                        <div className="font-medium">{city.name}</div>
                        <div className="text-sm text-gray-500">{city.country}</div>
                      </div>
                      {city.exists && (
                        <div className="text-xs text-green-600 bg-green-100 px-2 py-1 rounded">
                          Available
                        </div>
                      )}
                    </div>
                    
                    {!city.exists && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleAddCity(city)}
                        disabled={loading}
                        className="ml-2"
                      >
                        <Plus className="h-3 w-3 mr-1" />
                        Add
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 text-center text-gray-500">
                {query.length < 2 ? 'Type at least 2 characters to search' : 'No cities found'}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Click outside to close */}
      {showResults && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowResults(false)}
        />
      )}
    </div>
  );
};

export default CitySearch;