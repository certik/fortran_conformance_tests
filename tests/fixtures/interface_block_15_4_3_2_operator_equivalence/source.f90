module interface_block_operator_equivalence_m
  implicit none
  ! rule: S15.4.3.2-001
  ! covers: OPERATOR(.LT.) opening matched by OPERATOR(<) ending
  type :: box
    integer :: value
  end type box
  interface operator(.lt.)
    module procedure less_box
  end interface operator(<)
contains
  logical function less_box(left, right)
    type(box), intent(in) :: left, right
    less_box = left%value < right%value
  end function less_box
  logical function false_less_box(left, right)
    type(box), intent(in) :: left, right
    false_less_box = .false.
  end function false_less_box
end module interface_block_operator_equivalence_m

program interface_block_operator_equivalence
  use interface_block_operator_equivalence_m
  implicit none
  type(box) :: low, high
  low%value = 1
  high%value = 2
  if (.not. (low < high)) error stop 1
  print '(a)', 'INTERFACE BLOCK OPERATOR EQUIVALENCE OK'
end program interface_block_operator_equivalence
