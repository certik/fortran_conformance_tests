program expr_c1002_whole_assumed_size
  implicit none
  integer :: actual(3) = [1,2,3]
  call observe(actual)
contains
  subroutine observe(a)
    integer, intent(in) :: a(*)
    integer :: b(3)
    b = a
  end subroutine observe
end program expr_c1002_whole_assumed_size
