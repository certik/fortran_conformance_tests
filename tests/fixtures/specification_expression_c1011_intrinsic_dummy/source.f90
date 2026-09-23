program specification_expression_c1011_intrinsic_dummy
  implicit none
  call observe(6, 7)
  call observe(3, 4)
  write(*,'(a)') 'SPECEXPR C1011 INTRINSIC DUMMY OK'
contains
  subroutine observe(n, expected)
    integer, intent(in) :: n, expected
    integer :: a((n+1))
    if (size(a) /= expected) error stop 'SEC1011:intrinsic-dummy'
  end subroutine observe
end program specification_expression_c1011_intrinsic_dummy
