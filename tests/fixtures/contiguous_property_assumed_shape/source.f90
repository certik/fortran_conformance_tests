program contiguous_property_assumed_shape
  implicit none
  integer :: a(-2:2,4:6)
  integer :: i, j
  do j=4,6
    do i=-2,2
      a(i,j)=1000+100*j+7*i
    end do
  end do
  call check(a)
  write(*,'(a)') 'CONTIGUOUS PROPERTY OK assumed_shape'
contains
  subroutine check(x)
    integer, intent(in) :: x(-2:,4:)
    integer :: sh(2)
    sh=shape(x)
  if (is_contiguous(x) .neqv. .true.) error stop 'CP:assumed-shape-contiguous'
  if (lbound(x,1) /= -2) error stop 'CP:lb1'
  if (ubound(x,1) /= 2) error stop 'CP:ub1'
  if (lbound(x,2) /= 4) error stop 'CP:lb2'
  if (ubound(x,2) /= 6) error stop 'CP:ub2'
  if (sh(1) /= 5) error stop 'CP:shape1'
  if (sh(2) /= 3) error stop 'CP:shape2'
  if (x(1,5) /= 1507) error stop 'CP:payload'
  end subroutine check
end program contiguous_property_assumed_shape
