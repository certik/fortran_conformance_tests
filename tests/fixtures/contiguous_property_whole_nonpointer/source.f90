program contiguous_property_whole_nonpointer
  implicit none
  integer :: a(-2:2,4:6)
  integer, allocatable :: empty(:)
  integer :: i, j, sh(2), esh(1)
  do j=4,6
    do i=-2,2
      a(i,j)=1000+100*j+7*i
    end do
  end do
  allocate(empty(5:4))
  sh=shape(a)
  esh=shape(empty)
  if (is_contiguous(a) .neqv. .true.) error stop 'CP:whole-contiguous'
  if (is_contiguous(empty) .neqv. .true.) error stop 'CP:zero-size-whole-contiguous'
  if (lbound(a,1) /= -2) error stop 'CP:lb1'
  if (ubound(a,1) /= 2) error stop 'CP:ub1'
  if (lbound(a,2) /= 4) error stop 'CP:lb2'
  if (ubound(a,2) /= 6) error stop 'CP:ub2'
  if (sh(1) /= 5) error stop 'CP:shape1'
  if (sh(2) /= 3) error stop 'CP:shape2'
  if (merge(1,2,allocated(empty)) /= 1) error stop 'CP:empty-allocated'
  if (esh(1) /= 0) error stop 'CP:empty-shape'
  if (a(2,6) /= 1614) error stop 'CP:payload'
  write(*,'(a)') 'CONTIGUOUS PROPERTY OK whole_nonpointer'
end program contiguous_property_whole_nonpointer
