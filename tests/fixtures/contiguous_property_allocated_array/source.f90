program contiguous_property_allocated_array
  implicit none
  integer, allocatable :: a(:,:), empty(:)
  integer, pointer :: pt(:)
  integer :: i, j, sh(2), esh(1), psh(1)
  allocate(a(-3:1,7:9))
  do j=7,9
    do i=-3,1
      a(i,j)=1000+100*j+7*i
    end do
  end do
  allocate(empty(8:7))
  allocate(pt(4:6))
  do i=4,6
    pt(i)=300+13*i
  end do
  sh=shape(a)
  esh=shape(empty)
  psh=shape(pt)
  if (is_contiguous(a) .neqv. .true.) error stop 'CP:allocatable-contiguous'
  if (is_contiguous(empty) .neqv. .true.) error stop 'CP:allocated-empty-contiguous'
  if (is_contiguous(pt) .neqv. .true.) error stop 'CP:allocated-pointer-target-contiguous'
  if (merge(1,2,allocated(a)) /= 1) error stop 'CP:allocated'
  if (merge(1,2,associated(pt)) /= 1) error stop 'CP:pt-associated'
  if (lbound(a,1) /= -3) error stop 'CP:lb1'
  if (ubound(a,1) /= 1) error stop 'CP:ub1'
  if (lbound(a,2) /= 7) error stop 'CP:lb2'
  if (ubound(a,2) /= 9) error stop 'CP:ub2'
  if (sh(1) /= 5) error stop 'CP:shape1'
  if (sh(2) /= 3) error stop 'CP:shape2'
  if (esh(1) /= 0) error stop 'CP:empty-shape'
  if (lbound(pt,1) /= 4) error stop 'CP:pt-lb'
  if (ubound(pt,1) /= 6) error stop 'CP:pt-ub'
  if (psh(1) /= 3) error stop 'CP:pt-shape'
  if (a(-2,8) /= 1786) error stop 'CP:payload'
  if (pt(5) /= 365) error stop 'CP:pt-payload'
  write(*,'(a)') 'CONTIGUOUS PROPERTY OK allocated_array'
end program contiguous_property_allocated_array
