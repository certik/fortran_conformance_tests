program specification_expression_p1_contexts
  implicit none
  integer, parameter :: k=7
  integer :: a(k)
  if (size(a) /= 7) error stop 'SEP1:constant'
  call observe(7, 7)
  call observe(4, 4)
  write(*,'(a)') 'SPECEXPR P1 CONTEXTS OK'
contains
  subroutine observe(n, expected)
    integer, intent(in) :: n, expected
    integer :: dynamic(n)
    if (size(dynamic) /= expected) error stop 'SEP1:subprogram'
  end subroutine observe
end program specification_expression_p1_contexts
