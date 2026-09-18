program assumed_rank_expression_context
  implicit none
  integer :: subject
  subject=7
  call observe(subject)
contains
  subroutine observe(x)
    implicit none
    integer, intent(in) :: x(..)
    print *, x
  end subroutine observe
end program assumed_rank_expression_context
