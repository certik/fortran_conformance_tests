program pointer_assignment_syntax_kind_mismatch
  implicit none
  type :: box(k)
    integer, kind :: k
    integer :: value
  end type box
  type(box(1)), pointer :: p
  type(box(2)), target :: t
  p => t
end program pointer_assignment_syntax_kind_mismatch
