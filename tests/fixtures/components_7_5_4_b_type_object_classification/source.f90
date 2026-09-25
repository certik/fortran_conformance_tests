program component_type_object_classification
implicit none
type :: leaf
  integer :: value = 5
end type
type(leaf), target, save :: target_leaf = leaf(8)
type :: wrapper
  type(leaf) :: nested
  type(leaf), pointer :: link => null()
  type(leaf), allocatable :: bucket
end type
type(wrapper) :: item
if (item%nested%value /= 5) error stop 1
if (associated(item%link)) error stop 2
if (allocated(item%bucket)) error stop 3
print '(a)', 'COMPONENTS 7.5.4B CLASSIFICATION OK'
end program
