      program fixed_source
      implicit none
      integer first, second
      first = 1
     1  + 2
      second = 4
C     A comment does not terminate the continued statement.
     !  + 5
      if (first .ne. 3) stop 1
      if (second .ne. 9) stop 2
      write(*,'(a,ss,i0,a,i0)') 'FIXED=', first, ',', second
      end
