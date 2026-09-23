program specification_expression_c1011_standard_intrinsic
  implicit none
  call observe(7, 7)
  call observe(0, 1)
  write(*,'(a)') 'SPECEXPR C1011 STANDARD INTRINSIC OK'
contains
  subroutine observe(n, expected)
    integer, intent(in) :: n, expected
    integer :: a(max(n,1))
    if (size(a) /= expected) error stop 'SEC1011:max'
  end subroutine observe
end program specification_expression_c1011_standard_intrinsic
