program component_common_overrides
implicit none
type :: record
  character(5) :: short*2, common
  integer, dimension(3) :: local(2), shared
end type
type(record) :: item
item%short = 'xy'
item%common = 'abcde'
item%local = 0
item%shared = 0
if (len(item%short) /= 2) error stop 1
if (len(item%common) /= 5) error stop 2
if (size(item%local) /= 2) error stop 3
if (size(item%shared) /= 3) error stop 4
print '(a)', 'COMPONENTS 7.5.4B OVERRIDES OK'
end program
