program contiguous_property_multidimensional_interleaving
  implicit none
  integer :: a(1:3,5:7)
  integer :: i, j, sh(2), gapsh(2)
  do j=5,7
    do i=1,3
      a(i,j)=1000+100*j+7*i
    end do
  end do
  sh=shape(a(:,5:6))
  gapsh=shape(a(1:2,5:6))
  if (is_contiguous(a(:,5:6)) .neqv. .true.) error stop 'CP:positive-control-contiguous'
  if (is_contiguous(a(1:2,5:6)) .neqv. .false.) error stop 'CP:interleaved-section-not-contiguous'
  if (sh(1) /= 3) error stop 'CP:positive-shape1'
  if (sh(2) /= 2) error stop 'CP:positive-shape2'
  if (lbound(a(1:2,5:6),1) /= 1) error stop 'CP:gap-lb1'
  if (ubound(a(1:2,5:6),1) /= 2) error stop 'CP:gap-ub1'
  if (lbound(a(1:2,5:6),2) /= 1) error stop 'CP:gap-lb2'
  if (ubound(a(1:2,5:6),2) /= 2) error stop 'CP:gap-ub2'
  if (gapsh(1) /= 2) error stop 'CP:gap-shape1'
  if (gapsh(2) /= 2) error stop 'CP:gap-shape2'
  if (a(1,5) /= 1507) error stop 'CP:gap-first'
  if (a(2,6) /= 1614) error stop 'CP:gap-last'
  write(*,'(a)') 'CONTIGUOUS PROPERTY OK multidimensional_interleaving'
end program contiguous_property_multidimensional_interleaving
