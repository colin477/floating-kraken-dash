import { useState, useRef, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { X, Plus } from 'lucide-react';

interface AutocompleteFieldProps {
  label: string;
  placeholder: string;
  options: string[];
  selectedItems: string[];
  onSelectionChange: (items: string[]) => void;
  maxHeight?: string;
}

export const AutocompleteField = ({ 
  label, 
  placeholder, 
  options, 
  selectedItems, 
  onSelectionChange,
  maxHeight = "max-h-48"
}: AutocompleteFieldProps) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const [filteredOptions, setFilteredOptions] = useState<string[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Filter options based on search term and exclude already selected items
  useEffect(() => {
    if (searchTerm.trim().length > 0) {
      const filtered = options
        .filter(option => 
          option.toLowerCase().includes(searchTerm.toLowerCase()) &&
          !selectedItems.includes(option)
        )
        .slice(0, 10); // Limit to 10 results
      
      setFilteredOptions(filtered);
      setShowDropdown(filtered.length > 0);
      setSelectedIndex(-1);
    } else {
      setFilteredOptions([]);
      setShowDropdown(false);
    }
  }, [searchTerm, options, selectedItems]);

  // Handle clicking outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        inputRef.current && 
        !inputRef.current.contains(event.target as Node) &&
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleAddItem = (item: string) => {
    if (item.trim() && !selectedItems.includes(item.trim())) {
      onSelectionChange([...selectedItems, item.trim()]);
    }
    setSearchTerm('');
    setShowDropdown(false);
    setSelectedIndex(-1);
  };

  const handleRemoveItem = (itemToRemove: string) => {
    onSelectionChange(selectedItems.filter(item => item !== itemToRemove));
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showDropdown) {
      if (e.key === 'Enter' && searchTerm.trim()) {
        e.preventDefault();
        handleAddItem(searchTerm);
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < filteredOptions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => prev > 0 ? prev - 1 : -1);
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0) {
          handleAddItem(filteredOptions[selectedIndex]);
        } else if (searchTerm.trim()) {
          handleAddItem(searchTerm);
        }
        break;
      case 'Escape':
        setShowDropdown(false);
        setSelectedIndex(-1);
        break;
    }
  };

  const handleOptionClick = (option: string) => {
    handleAddItem(option);
  };

  const highlightMatch = (text: string, query: string) => {
    if (!query) return text;
    
    const index = text.toLowerCase().indexOf(query.toLowerCase());
    if (index === -1) return text;
    
    return (
      <>
        {text.substring(0, index)}
        <span className="bg-yellow-200 font-medium">
          {text.substring(index, index + query.length)}
        </span>
        {text.substring(index + query.length)}
      </>
    );
  };

  return (
    <div className="space-y-3">
      <div className="relative">
        <Input
          ref={inputRef}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="pr-10"
        />
        
        {searchTerm && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="absolute right-1 top-1/2 transform -translate-y-1/2 h-8 w-8 p-0"
            onClick={() => handleAddItem(searchTerm)}
          >
            <Plus className="h-4 w-4" />
          </Button>
        )}

        {/* Dropdown */}
        {showDropdown && filteredOptions.length > 0 && (
          <div
            ref={dropdownRef}
            className={`absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg ${maxHeight} overflow-y-auto`}
          >
            {filteredOptions.map((option, index) => (
              <div
                key={option}
                className={`px-3 py-2 cursor-pointer text-sm hover:bg-gray-100 ${
                  index === selectedIndex ? 'bg-blue-50 text-blue-700' : ''
                }`}
                onClick={() => handleOptionClick(option)}
                onMouseEnter={() => setSelectedIndex(index)}
              >
                {highlightMatch(option, searchTerm)}
              </div>
            ))}
            
            {/* Add custom option */}
            {searchTerm && !filteredOptions.some(opt => opt.toLowerCase() === searchTerm.toLowerCase()) && (
              <div
                className={`px-3 py-2 cursor-pointer text-sm hover:bg-gray-100 border-t border-gray-200 ${
                  selectedIndex === filteredOptions.length ? 'bg-blue-50 text-blue-700' : ''
                }`}
                onClick={() => handleAddItem(searchTerm)}
              >
                <div className="flex items-center">
                  <Plus className="h-3 w-3 mr-2" />
                  Add "{searchTerm}"
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Selected Items */}
      {selectedItems.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {selectedItems.map(item => (
            <Badge key={item} variant="secondary" className="text-sm">
              {item}
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="ml-1 h-4 w-4 p-0 hover:bg-transparent"
                onClick={() => handleRemoveItem(item)}
              >
                <X className="h-3 w-3" />
              </Button>
            </Badge>
          ))}
        </div>
      )}

      <p className="text-xs text-gray-500">
        Start typing to search, press Enter to add custom items, or select from suggestions
      </p>
    </div>
  );
};