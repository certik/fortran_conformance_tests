program component_character_suffix
implicit none
type :: record
  character :: star*3
end type
type(record) :: item
item%star = 'abc'
if (len(item%star) /= 3) error stop 1
if (item%star /= 'abc') error stop 2
print '(a)', 'COMPONENTS 7.5.4B CHAR SUFFIX OK'
end program
