class Solution(object):
    def threeSum(self, nums):
        """
        :type nums: List[int]
        :rtype: List[List[int]]
        """
        nums = [0,0,0]
        # nums = [0,1,1]
        # nums = [-1,0,1,2,-1,-4]
        sample_space = {}
        for x in range(0, len(nums)):
            for y in range(0, len(nums)):
                if not x == y:
                    for z in range(0, len(nums)):
                        if all([x != y, x != z, y != z]):
                            value = nums[x] + nums[y] + nums[z]
                            if value:
                                key = (x,y,z)
                                sample_space(key) = value
        output = [index for index,val in sample_space.items() ]
        return output
                            

            
        