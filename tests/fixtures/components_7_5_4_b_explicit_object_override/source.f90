program component_explicit_object_override
implicit none
type :: record
  integer :: value = 7
end type
type(record) :: explicit = record(19)
type(record) :: defaulted
if (explicit%value /= 19) error stop 1
if (defaulted%value /= 7) error stop 2
print '(a)', 'COMPONENTS 7.5.4B EXPLICIT OVERRIDE OK'
end program
