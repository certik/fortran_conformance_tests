module specification_expression_p4_functions
  implicit none
contains
  pure integer function width(i)
    integer, intent(in) :: i
    width=i+3
  end function width
end module specification_expression_p4_functions
program specification_expression_p4_spec_function
  use specification_expression_p4_functions, only: width
  implicit none
  call observe(4, 7)
  call observe(7, 10)
  write(*,'(a)') 'SPECEXPR P4 SPEC FUNCTION OK'
contains
  subroutine observe(n, expected)
    integer, intent(in) :: n, expected
    integer :: a(width(n))
    if (size(a) /= expected) error stop 'SEP4:spec-function'
  end subroutine observe
end program specification_expression_p4_spec_function
