program contiguous_property_full_leading_dimensions
  implicit none
  integer :: a(-2:2,4:7)
  integer :: i, j, sh(2)
  do j=4,7
    do i=-2,2
      a(i,j)=1000+100*j+7*i
    end do
  end do
  sh=shape(a(:,4:5))
  if (is_contiguous(a(:,4:5)) .neqv. .true.) error stop 'CP:full-leading-section-contiguous'
  if (lbound(a(:,4:5),1) /= 1) error stop 'CP:lb1'
  if (ubound(a(:,4:5),1) /= 5) error stop 'CP:ub1'
  if (lbound(a(:,4:5),2) /= 1) error stop 'CP:lb2'
  if (ubound(a(:,4:5),2) /= 2) error stop 'CP:ub2'
  if (sh(1) /= 5) error stop 'CP:shape1'
  if (sh(2) /= 2) error stop 'CP:shape2'
  if (a(2,5) /= 1514) error stop 'CP:payload'
  write(*,'(a)') 'CONTIGUOUS PROPERTY OK full_leading_dimensions'
end program contiguous_property_full_leading_dimensions
