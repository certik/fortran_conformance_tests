program component_individual_declarators
implicit none
type :: record
  integer :: values(2)
  character(5) :: text*3
  integer :: initial = 7
end type
type(record) :: item
item%values = 0
item%text = 'abc'
if (size(item%values) /= 2) error stop 1
if (len(item%text) /= 3) error stop 2
if (item%text /= 'abc') error stop 3
if (item%initial /= 7) error stop 4
print '(a)', 'COMPONENTS 7.5.4B DECLARATORS OK'
end program
