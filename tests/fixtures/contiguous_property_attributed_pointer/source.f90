program contiguous_property_attributed_pointer
  implicit none
  integer, target :: a(-2:2,4:6)
  integer, pointer, contiguous :: ptr(:,:)
  integer :: i, j, sh(2)
  do j=4,6
    do i=-2,2
      a(i,j)=1000+100*j+7*i
    end do
  end do
  ptr(-2:,4:) => a
  sh=shape(ptr)
  if (is_contiguous(ptr) .neqv. .true.) error stop 'CP:attributed-contiguous'
  if (lbound(ptr,1) /= -2) error stop 'CP:lb1'
  if (ubound(ptr,1) /= 2) error stop 'CP:ub1'
  if (lbound(ptr,2) /= 4) error stop 'CP:lb2'
  if (ubound(ptr,2) /= 6) error stop 'CP:ub2'
  if (sh(1) /= 5) error stop 'CP:shape1'
  if (sh(2) /= 3) error stop 'CP:shape2'
  if (ptr(-1,5) /= 1493) error stop 'CP:payload'
  write(*,'(a)') 'CONTIGUOUS PROPERTY OK attributed_pointer'
end program contiguous_property_attributed_pointer
