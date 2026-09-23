module specification_expression_c1011_functions
  implicit none
contains
  pure integer function add_two(i)
    integer, intent(in) :: i
    add_two=i+2
  end function add_two
end module specification_expression_c1011_functions
program specification_expression_c1011_spec_function
  use specification_expression_c1011_functions, only: add_two
  implicit none
  call observe(5, 7)
  call observe(2, 4)
  write(*,'(a)') 'SPECEXPR C1011 SPEC FUNCTION OK'
contains
  subroutine observe(n, expected)
    integer, intent(in) :: n, expected
    integer :: a(add_two(n))
    if (size(a) /= expected) error stop 'SEC1011:spec-function'
  end subroutine observe
end program specification_expression_c1011_spec_function
