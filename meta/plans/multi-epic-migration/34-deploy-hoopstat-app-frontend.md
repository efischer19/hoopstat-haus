# feat: Deploy hoopstat-app frontend to S3/CloudFront

## What do you want to build?

Deploy the hoopstat-app frontend to its S3 bucket and verify it's accessible via CloudFront. This makes the new frontend live, though DNS will still point to the old infrastructure until the Route53 cutover.

## Acceptance Criteria

- [ ] The deploy-aws workflow runs successfully in hoopstat-app
- [ ] Frontend files are synced to the correct S3 bucket
- [ ] CloudFront distribution serves the frontend correctly
- [ ] The site is accessible via the CloudFront distribution domain name (e.g., `d1234.cloudfront.net`)
- [ ] All pages render correctly (main dashboard, health dashboard)
- [ ] JavaScript loads data from the gold layer endpoints successfully
- [ ] No CORS errors in the browser console
- [ ] CloudFront cache invalidation completes
- [ ] The deployment is repeatable (running the workflow again produces the same result)

## Implementation Notes (Optional)

**Pre-deployment checklist:**
Before deploying:
1. ✅ hoopstat-app repo has the AWS_ROLE_ARN variable set (ticket 32)
2. ✅ The S3 bucket exists (created by hoopstat-data's Terraform or separately)
3. ✅ The CloudFront distribution exists and is configured
4. ✅ The frontend code is merged to main in hoopstat-app

**Data endpoint configuration:**
The frontend JavaScript files fetch data from CloudFront-served gold layer endpoints. These URLs must be correct:
- If using the same CloudFront distribution as before: URLs don't need to change
- If using a new distribution: Update the base URL in the JavaScript files

**Testing the deployment:**
1. Access the CloudFront distribution URL directly (not the custom domain yet)
2. Verify all pages load
3. Check browser DevTools Network tab for failed requests
4. Check the Console tab for JavaScript errors
5. Verify charts render with real data

**CORS considerations:**
If the frontend and data are on different CloudFront distributions, CORS headers must be configured on the data distribution. This is handled by the CloudFront Origin Request Policy (reference ADR-035 and hoopstat-haus's `CORS-S3Origin` configuration).

The custom domain (hoopstat.haus) will be pointed to this deployment in ticket 35 (Route53 cutover).
